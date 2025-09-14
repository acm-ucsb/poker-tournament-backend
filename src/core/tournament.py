from postgrest import APIError
from src.util.supabase_client import db_client
from src.core.table import Table


class Tournament:
    def __init__(self, tournament_id: str = "f6fd507b-42fb-4fba-a0d3-e9ded05aeca5"):
        try:
            status_res = (
                db_client.table("tournaments")
                .select("status", "table")
                .eq("id", tournament_id)
                .single()
                .execute()
            )

            self.tournament_id: str = tournament_id
            self.status: str = status_res.data["status"]

            table_ids: list[str] = status_res.data["tables"]
            self.tables = list(map(lambda t: Table(t), table_ids))

        except APIError:
            raise ValueError(f"Tournament with id {tournament_id} does not exist.")

    def matchmake(self):
        # ASSUMING ALL TEAMS IN TEAMS (supabase table) ARE ALLOWED TO BE MATCHED INTO TOURNEY
        pass
