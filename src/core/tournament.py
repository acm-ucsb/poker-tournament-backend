from src.util.supabase_client import db_client
from src.core.table import Table
import random
import math

import traceback

MAX_TABLE_SIZE = 9
DEFAULT_TOURNAMENT_ID = "f6fd507b-42fb-4fba-a0d3-e9ded05aeca5"

BLIND_INCREASE = 2


class Tournament:
    @staticmethod
    def exists_tournament(id: str = DEFAULT_TOURNAMENT_ID) -> bool:
        try:
            res = (
                db_client.table("tournaments")
                .select("id")
                .eq("id", id)
                .single()
                .execute()
            )
            return res.data["id"] == id
        except Exception:
            return False

    @staticmethod
    def insert_tournament(id: str = DEFAULT_TOURNAMENT_ID):
        db_client.table("tournaments").insert(
            {
                "id": id,
                "name": "New Tournament",
                "status": "not_started",
            }
        ).execute()

    # syncs internal state of tournament from db
    def _sync_tables(self):
        status_res = (
            db_client.table("tournaments")
            .select("status", "tables")
            .eq("id", self.tournament_id)
            .single()
            .execute()
        )
        table_ids: list[str] = status_res.data["tables"] or []
        table_objs = list(map(lambda t: Table(t), table_ids))

        self.tables = dict(zip(table_ids, table_objs))

    def __init__(self, tournament_id: str = DEFAULT_TOURNAMENT_ID):
        self.tournament_id: str = tournament_id
        self.tables: dict[str, Table] = {}

        self._sync_tables()

    # INSERTS ALL POSSIBLE TABLES INTO DB, ASSIGNS TABLES TO DEFAULT TOURNAMENT
    def insert_tables(self):
        # ASSUMING ALL TEAMS IN TEAMS (supabase table) ARE ALLOWED TO BE MATCHED INTO TOURNEY
        teams_res = (
            db_client.table("teams")
            .select("id")
            .eq("has_submitted_code", True)
            .eq("is_disqualified", False)
            .execute()
        )

        teams: list[str] = []
        for team in teams_res.data:
            teams.append(team["id"])
        random.shuffle(teams)

        if len(teams) == 0:
            # no teams exist
            db_client.table("tournaments").update({"tables": []}).eq(
                "id", self.tournament_id
            ).execute()
        else:
            num_groups = math.ceil(len(teams) / MAX_TABLE_SIZE)
            chunk_len = len(teams) // num_groups
            rem = len(teams) % num_groups

            table_ids: list[str] = []

            for i in range(num_groups):
                idx = i * chunk_len + ((i + 1) if i < rem else rem)
                table_sublist = teams[idx : idx + chunk_len + (1 if i < rem else 0)]
                new_table_id = Table.insert(table_sublist, self.tournament_id)
                table_ids.append(new_table_id)

            # set the tables in the tournament
            db_client.table("tournaments").update({"tables": table_ids}).eq(
                "id", self.tournament_id
            ).execute()

        self._sync_tables()

    # DELETES ALL TABLES, AND TABLES COL IN TOURNAMENT
    def delete_tables(self):
        # delete all entries in tables (realistically tables wont have this id)
        db_client.table("tables").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        # delete tables to update in the tournament entry
        db_client.table("tournaments").update({"tables": None}).eq(
            "id", self.tournament_id
        ).execute()

        self._sync_tables()

    async def make_moves(
        self, table_ids: list[str] | None = None, moves: list[int] | None = None, /
    ):
        # table_ids to specify which tables to make moves on, default None for make_move on all
        # moves is for human moves so must be same len as table_ids, default None for no human moves
        result_strs = []

        for table in self.tables.values():
            try:
                result_strs.append(await table.make_move())
            except BaseException as e:
                print(e)
                result_strs.append(
                    f"did not run, {e}, {e.args}, {e.with_traceback(None)}, {traceback.format_exc()}"
                )

        return result_strs

    def increase_blind_of_all_tables(self):
        # increases blinds of all tables by BLIND_INCREASE factor
        for id in self.tables:
            self.tables[id].state.small_blind = int(
                self.tables[id].state.small_blind * BLIND_INCREASE
            )
            self.tables[id].state.big_blind = int(
                self.tables[id].state.big_blind * BLIND_INCREASE
            )

            Table.write_state_to_db(id, self.tables[id].state)

        self._sync_tables()


# main instance!!!
tournament = None
if not Tournament.exists_tournament():
    Tournament.insert_tournament()
tournament = Tournament()
