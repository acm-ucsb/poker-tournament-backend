import json
from postgrest import APIError
from src.util.models import GameState
from src.util.supabase_client import db_client


class Table:
    def _read_state_from_db(self, table_id: str):
        try:
            state_res = (
                db_client.table("tables")
                .select("game_state")
                .eq("id", table_id)
                .single()
                .execute()
            )

            state_dict = json.loads(state_res.data["game_state"])

            return GameState(**state_dict)

        except APIError:
            raise ValueError(f"Table with id {table_id} does not exist.")

    def _write_state_to_db(self):
        update_json = {"game_state": self.state}

        try:
            db_client.table("tables").update(update_json).eq(
                "id", self.table_id
            ).execute()
        except APIError:
            raise ValueError(f"Table with id {self.table_id} does not exist.")

    def __init__(self, table_id: str):
        self.table_id: str = table_id
        self.state: GameState = self._read_state_from_db(table_id)

    def is_valid_move(self, action: float):
        pass

    # -1 = fold, 0 check, >0 bet
    def make_move(self, action: float):
        self._write_state_to_db()
