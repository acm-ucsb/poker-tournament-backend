from src.util.supabase_client import db_client
from src.core.table import Table
import random
import math

MAX_TABLE_SIZE = 9
DEFAULT_TOURNAMENT_ID = "f6fd507b-42fb-4fba-a0d3-e9ded05aeca5"


class Tournament:
    @staticmethod
    def exists_tournament(id: str = DEFAULT_TOURNAMENT_ID) -> bool:
        try:
            db_client.table("tournaments").select("id").eq("id", id).execute()
            return True
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

    # INSERTS ALL POSSIBLE TABLES INTO DB, ASSIGNS TABLES TO DEFAULT TOURNAMENT
    @staticmethod
    def insert_tables():
        # ASSUMING ALL TEAMS IN TEAMS (supabase table) ARE ALLOWED TO BE MATCHED INTO TOURNEY
        teams_res = (
            db_client.table("teams")
            .select("id")
            .eq("has_submitted_code", True)
            .execute()
        )

        teams: list[str] = []
        for team in teams_res.data:
            teams.append(team["id"])
        random.shuffle(teams)

        num_groups = math.ceil(len(teams) / MAX_TABLE_SIZE)
        chunk_len = len(teams) // num_groups
        rem = len(teams) % num_groups

        table_ids: list[str] = []

        for i in range(num_groups):
            idx = i * chunk_len + ((i + 1) if i < rem else rem)
            table_sublist = teams[idx : idx + chunk_len + (1 if i < rem else 0)]
            new_table_id = Table.insert(table_sublist)
            table_ids.append(new_table_id)

        # set the tables in the tournament
        db_client.table("tournaments").update({"tables": table_ids}).eq(
            "id", DEFAULT_TOURNAMENT_ID
        ).execute()

    # DELETES ALL TABLES, AND TABLES COL IN TOURNAMENT
    @staticmethod
    def delete_tables():
        # delete all entries in tables (realistically tables wont have this id)
        db_client.table("tables").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        # delete tables to update in the tournament entry
        db_client.table("tournaments").update({"tables": None}).eq(
            "id", DEFAULT_TOURNAMENT_ID
        ).execute()

    def __init__(self, tournament_id: str = DEFAULT_TOURNAMENT_ID):
        status_res = (
            db_client.table("tournaments")
            .select("status", "tables")
            .eq("id", tournament_id)
            .single()
            .execute()
        )

        self.tournament_id: str = tournament_id
        self.status: str = status_res.data["status"]

        table_ids: list[str] = status_res.data["tables"] or []
        table_objs = list(map(lambda t: Table(t), table_ids))

        self.tables = dict(zip(table_ids, table_objs))

    async def make_moves(
        self, table_ids: list[str] | None = None, moves: list[float] | None = None, /
    ):
        # table_ids to specify which tables to make moves on, default None for make_move on all
        # moves is for human moves so must be same len as table_ids, default None for no human moves
        result_strs = []

        if table_ids is not None and moves is not None:
            for id, move in zip(table_ids, moves):
                result_strs.append(await self.tables[id].make_move(move))
        elif table_ids is not None:
            for id in table_ids:
                result_strs.append(await self.tables[id].make_move())
        else:
            for table in self.tables.values():
                result_strs.append(await table.make_move())

        return result_strs


# main instance!!!
tournament = None
if not Tournament.exists_tournament():
    Tournament.insert_tournament()
tournament = Tournament()
