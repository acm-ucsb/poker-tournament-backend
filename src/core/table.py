import json
import random
from src.util.models import GameState, Pot
from src.util.supabase_client import db_client
from typing import Any
import copy

DEFUALT_SB = 5.0
DEFAULT_BB = 10.0

RANKS = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "t", "j", "q", "k"]
SUITS = ["s", "d", "c", "h"]
FULL_DECK = [rank + suit for suit in SUITS for rank in RANKS]


class Table:
    # shuffled, pulled from a GameState, or defualt all possible cards
    # for drawing random cards.
    @staticmethod
    def available_cards_shuffled(s: GameState | None = None) -> list[str]:
        def shuffle_copy(li: list[Any]):
            return random.sample(li, len(li))

        if s is None:
            return shuffle_copy(FULL_DECK)

        # pull all used cards from state
        used_cards = s.community_cards.copy()
        for c in s.players_cards:
            used_cards += c

        # set difference
        diff = list(set(FULL_DECK) - set(used_cards))
        return shuffle_copy(diff)

    @staticmethod
    def rotate_positions(s: GameState):
        # technically deque is more efficient... but it don't matter
        s.players.append(s.players.pop(0))
        s.held_money.append(s.held_money.pop(0))

    # in-place to the GameState
    # raise_size: -1 = fold, 0 check, >0 raise their own bet amt
    # TODO: sidepots for all-ins, winner, last one standing
    @staticmethod
    def apply_bet(s: GameState, raise_size: float, is_blind=False):
        action_result = f"raised bet by {raise_size}"  # temp result string

        def fold():
            s.bet_money[s.index_to_action] = -1
            for p in s.pots:
                player = s.players[s.index_to_action]
                if player in p.players:
                    p.players.remove(player)

        def push_index_to_action():
            while True:
                s.index_to_action += 1
                s.index_to_action %= len(s.players)
                if s.bet_money[s.index_to_action] != -1:
                    break

        # last one standing in entire game!
        if len(s.players) == 1:
            action_result = "table won. last one standing."
            return action_result

        max_bet = max(s.bet_money)
        total_bet = s.bet_money[s.index_to_action] + raise_size

        # check for: enough money condition, bet calls max_bet, bet raises with at least min raise (2x)
        if s.held_money[s.index_to_action] >= raise_size and (
            total_bet == max_bet or total_bet >= 2 * max_bet
        ):
            curr_team = s.players[s.index_to_action]
            if curr_team in s.pots[0].players:  # 0-th pot is the main pot
                s.pots[0].value += raise_size

                # adjust money values, held -> bet
                s.held_money[s.index_to_action] -= raise_size
                s.bet_money[s.index_to_action] += raise_size
            else:
                # not in main pot for some reason??
                fold()
                action_result = "invalid action. autofold."
        else:
            # autofold cuz invalid
            fold()
            action_result = "invalid action. autofold."

        # check if can move onto next betting round (meaning all people called max_bet, folded, or hold no more money)
        round_over = True
        for i in range(len(s.players)):
            if not (
                s.bet_money[i] == max_bet
                or s.bet_money[i] == -1
                or s.held_money[i] == 0
            ):
                round_over = False
        # exception: big blind in preflop can raise/check
        if round_over:
            available_cards = Table.available_cards_shuffled(s)
            # reveal new cards
            if len(s.community_cards) == 0:
                s.community_cards += available_cards[:3]
            elif len(s.community_cards) < 5:
                s.community_cards += available_cards[:1]
            else:
                # TODO: showdown. determine winner. distribute pots.
                for p in s.pots:
                    # determine_winner()
                    pass
                pass
        else:
            push_index_to_action()

        return action_result  # temp for result string

    # CREATES TABLE
    # INSERTS TABLE ENTRY INTO DB, RETURNS TABLE ID
    @staticmethod
    def insert(team_ids: list[str]) -> str:
        # insert row into db
        # new table
        cards = Table.available_cards_shuffled()
        if len(cards) < 2 * len(team_ids):
            raise ValueError(
                f"Too many teams ({team_ids}) in table to distribute two cards to each team ({len(cards)} cards remaining)."
            )

        players_cards = []
        held_money = []
        bet_money = []
        main_pot = Pot(value=0, players=team_ids)

        for _ in team_ids:
            players_cards.append([cards.pop(), cards.pop()])
            held_money.append(1000)
            bet_money.append(0)

        new_state = GameState(
            index_to_action=0,
            players=team_ids,
            players_cards=players_cards,
            held_money=held_money,
            bet_money=bet_money,
            community_cards=[],
            pots=[main_pot],
            current_round="preflop",
            small_blind=DEFUALT_SB,
            big_blind=DEFAULT_BB,
        )

        Table.apply_bet(new_state, new_state.small_blind)
        Table.apply_bet(new_state, new_state.big_blind)

        # write new entry into tables db
        row_entry_json = {"status": "active", "game_state": new_state.model_dump_json()}
        entry_res = db_client.table("tables").insert(row_entry_json).execute()
        table_id: str = entry_res.data[0]["id"]

        # set all table_id in teams table
        update_json = {"table_id": table_id}
        for team_id in team_ids:
            db_client.table("teams").update(update_json).eq("id", team_id).execute()

        return table_id

    @staticmethod
    def read_state_from_db(table_id: str):
        state_res = (
            db_client.table("tables")
            .select("game_state")
            .eq("id", table_id)
            .single()
            .execute()
        )
        state_dict = json.loads(state_res.data["game_state"])
        return GameState(**state_dict)

    @staticmethod
    def write_state_to_db(table_id: str, state: GameState):
        update_json = {"game_state": state}
        db_client.table("tables").update(update_json).eq("id", table_id).execute()

    def __init__(self, table_id: str):
        self.table_id: str = table_id
        self.state: GameState = Table.read_state_from_db(table_id)
        self.small_blind = 5
        self.big_blind = 10

    def make_move(self):  # TODO
        # stuff here, human or bot move
        # blinding, uh other stuff too i forgor
        action = 0
        Table.apply_bet(self.state, action)

        # modify self.state based on the action
        Table.write_state_to_db(self.table_id, self.state)

    def get_visible_state(self):
        visible_state = copy.deepcopy(self.state)
        visible_state.players_cards.clear()
        return visible_state
