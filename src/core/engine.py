from __future__ import annotations

from typing import TYPE_CHECKING

import multiprocessing

from src.core.player import Player
from src.core.table import Table, TableStatus
from src.core.matchmaking import Matchmaking
from src.util.supabase_client import db_client

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event
    from multiprocessing import Process


class Engine:
    _instance = None
    _lock = multiprocessing.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._is_initialized = True
        self._is_set_upped = False
        self.processes: dict[str, tuple[Process, Event]] = {}

        self.tables: dict[str, Table] = {}
        self.players: list[Player] = []
        self.matchmaking = Matchmaking()

    @staticmethod
    def _worker(table: Table, event: Event):
        while event.is_set():
            table.run()
            # TODO: table handel table reassign
            if table.status == TableStatus.inactive:
                break

        table.close()

    def _setup(self):
        if self.processes:
            raise Exception("Can not reset engine while engine is running.")
        if self._is_set_upped:
            return -1

        db_client.table("teams").select("")

        response = (
            db_client.table("teams")
            .select("*")
            .eq("has_submitted_code", True)
            .eq("submission_passed", True)
            .eq("is_disqualified", False)
            .execute()
        )

        self.players = [
            Player(player["id"], player["num_chips"]) for player in response.data
        ]

        self.matchmaking.add_players(self.players)
        self.tables = self.matchmaking.assign_table()

        db_client.table("tables").insert(
            [
                {
                    "id": table.id,
                    "status": "not_started",
                    "name": table.name,
                    "game_state": table.state,
                    "last_change": {},
                }
                for table in self.tables.values()
            ]
        ).execute()

        # TODO: optimize this by creating a postgres fn and calling it val .rpc()
        for table in self.tables.values():
            for player in table.players:
                db_client.table("teams").update({"table_id": table.id}).eq(
                    "id", player.id
                ).execute()

        self._is_set_upped = True

    def _reset(self):
        if self.processes:
            raise Exception("Can not reset engine while engine is running.")

        # TODO: optimize this by creating a postgres fn and calling it val .rpc()
        for table in self.tables.values():
            db_client.table("tables").update({"status": "inactive"}).eq(
                "id", table.id
            ).execute()

            for player in table.players:
                db_client.table("teams").update({"table_id": None}).eq(
                    "id", player.id
                ).execute()

        self.tables.clear()
        self.players.clear()

        self._is_set_upped = False

    def start(self) -> int:
        if self.processes:
            return -1

        self._reset()
        self._setup()

        for table in self.tables.values():
            event = multiprocessing.Event()
            p = multiprocessing.Process(
                target=self._worker, args=[event, table], daemon=True
            )
            self.processes[table.id] = (p, event)
            event.set()
            p.start()

        return 0

    def end(self) -> int:
        if not self.processes:
            return -1

        for _, event in self.processes.values():
            event.clear()

        for p, _ in self.processes.values():
            p.join()

        self.processes.clear()

        return 0

    def resume_tables(self, table_ids: list[str]) -> None:
        if len(table_ids) == 0:
            table_ids = [table_id for table_id in self.processes]

        for table_id in table_ids:
            self.tables[table_id].status = TableStatus.active
            self.processes[table_id][1].set()

    def pause_tables(self, table_ids: list[str]) -> None:
        if len(table_ids) == 0:
            table_ids = [table_id for table_id in self.processes]

        for table_id in table_ids:
            self.tables[table_id].status = TableStatus.paused
            self.processes[table_id][1].clear()
