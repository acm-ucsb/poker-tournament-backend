from src.util.supabase_client import db_client
from src.core.table import Table
import random
import math
from src.util.models import GameState


MAX_TABLE_SIZE = 9
DEFAULT_TOURNAMENT_ID = "f6fd507b-42fb-4fba-a0d3-e9ded05aeca5"


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
            .execute()
        )

        teams: list[str] = []
        for team in teams_res.data:
            teams.append(team["id"])
        random.shuffle(teams)

        if len(teams) == 0:
            # no teams exist
            db_client.table("tournaments").update({"tables": []}).eq(
                "id", DEFAULT_TOURNAMENT_ID
            ).execute()
        else:
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

        self._sync_tables()

    # DELETES ALL TABLES, AND TABLES COL IN TOURNAMENT
    def delete_tables(self):
        # delete all entries in tables (realistically tables wont have this id)
        db_client.table("tables").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        # delete tables to update in the tournament entry
        db_client.table("tournaments").update({"tables": None}).eq(
            "id", DEFAULT_TOURNAMENT_ID
        ).execute()

        self._sync_tables()

    async def make_moves(
        self, table_ids: list[str] | None = None, moves: list[int] | None = None, /
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
    
    # returns a list of all game states
    def retrieve_states(self):
        states = {}
        for id, table in self.tables.items():
            states[id] = table.read_state_from_db()
        return states
    
    def reassign(self):
        # determines if any of the tables need to be reassigned --> 
        # type 1 reassign -> close a table and reassign its players
        # type 2 reassign -> move around players to balance tables

        states = self.retrive_states()

        if (len(states) <= 1):
            return # no reassignment possible
        sizes = {id: Table.table_size(state) for id, state in states.items()}

        min_size = min(sizes.values())
        max_size = max(sizes.values())

        num_players = sum(sizes.values())

        min_tables = math.ceil(num_players / 8) # max table size
        max_tables = math.floor(num_players / 5)

        # Choose the smallest number of tables that fulfill table size constrains and table size only differ by 1
        for num_tables in range(min_tables, max_tables + 1):
            base_size, extra = divmod(num_players, num_tables)
            # if theres some leftover and add one to each table is within the constraints 
            # or if there aren't any extras and within constraints
            if (
                extra > 0
                and 5 <= (base_size + 1) <= 8
            ) or (5 <= base_size <= 8):
                break

        if num_tables == max_tables + 1:
            raise ValueError("Cannot distribute players within table size constraints.")
        
        if num_tables < len(states):
            smallest = [id for id, tb_size in sizes if tb_size == min_size][0] # smallest table id
            self.close_smallest_table(states, smallest)
    
    def close_smallest_table(self, states: list[GameState], table_id):
        available_seats = []

        for id, state in states.items():
            if id == table_id:
                continue
            for seat in Table.get_vacant_seats(state):
                available_seats.append((id, seat))

        available_seats.sort(key=lambda x: x[1]) # sort by seat priority

        players_to_reassign = []

        start = states[table_id].index_of_small_blind

        #players inserted in priority order
        for i in range(start+8, start, -1):
            idx = i%8
            if states[table_id].players[idx] != "":
                players_to_reassign.append((states[table_id].players[idx],
                                            states[table_id].held_money[idx]))

        idx = 0
        for player, held_money in players_to_reassign:
            if idx >= len(available_seats):
                raise ValueError("Not enough available seats to reassign players.")
            Table.insert_player(states[available_seats[idx][0]], player, held_money)
            # should never return false
            # insert players into tables based on priority

        # delete table from db
        db_client.table("tables").delete().neq(
            "id", table_id
        ).execute()
        
        table_ids = [id for id, state in states if id != table_id]
        db_client.table("tournaments").update({"tables": table_ids}).eq(
            "id", DEFAULT_TOURNAMENT_ID
        ).execute()






# main instance!!!
tournament = None
if not Tournament.exists_tournament():
    Tournament.insert_tournament()
tournament = Tournament()
