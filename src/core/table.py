import json
import random
from src.util.models import GameState, Pot
import src.util.helpers as helpers
from src.util.supabase_client import db_client
from typing import Any
import copy

from src.core.hand import FULL_DECK, Hand

DEFAULT_SB = 5
DEFAULT_BB = 10
DEFAULT_STARTING_STACK = 1000


class Table:
    # shuffled, pulled from a GameState, or default all possible cards
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
    def rotate_blinds(s: GameState):
        s.index_of_small_blind = (s.index_of_small_blind + 1) % len(s.players)

    # blind spots need sufficient money for blind values. main pot must exist.
    @staticmethod
    def apply_blinds(s: GameState):
        index_bb = (s.index_of_small_blind + 1) % len(s.players)
        index_utg = (s.index_of_small_blind + 2) % len(s.players)

        s.held_money[s.index_of_small_blind] -= s.small_blind
        s.bet_money[s.index_of_small_blind] += s.small_blind

        s.held_money[index_bb] -= s.big_blind
        s.bet_money[index_bb] += s.big_blind

        s.pots[0].value += s.small_blind + s.big_blind

        s.index_to_action = index_utg

    # in-place to the GameState
    # raise_size: -1 = fold, 0 check, >0 raise their own bet amt
    # TODO: last_change
    @staticmethod
    def apply_bet(s: GameState, raise_size: int):
        def fold():
            s.bet_money[s.index_to_action] = -1
            for p in s.pots:
                player = s.players[s.index_to_action]
                if player in p.players:
                    p.players.remove(player)

        def push_index_to_action():
            s.index_to_action = (s.index_to_action + 1) % len(s.players)
            while (
                s.bet_money[s.index_to_action] == -1
                or s.held_money[s.index_to_action] == 0
            ):
                s.index_to_action = (s.index_to_action + 1) % len(s.players)

        def new_round_set_index_to_action():
            s.index_to_action = s.index_of_small_blind
            while (
                s.bet_money[s.index_to_action] == -1
                or s.held_money[s.index_to_action] == 0
            ):
                s.index_to_action = (s.index_to_action + 1) % len(s.players)

        def new_hands():
            # removing players that have no more money.
            # popping in reverse so in-place removal has no issues
            for i in range(len(s.players) - 1, -1, -1):
                if s.held_money[i] == 0:
                    s.players.pop(i)
                    s.players_cards.pop(i)
                    s.held_money.pop(i)
                    s.bet_money.pop(i)

            for i in range(len(s.bet_money)):
                s.bet_money[i] = 0

            # deal new cards to players
            deck = Table.available_cards_shuffled()
            s.players_cards.clear()
            for i in range(len(s.players)):
                s.players_cards.append([deck.pop(), deck.pop()])

            s.community_cards.clear()
            s.pots = [Pot(value=0, players=s.players)]

            # blinds
            Table.rotate_blinds(s)
            Table.apply_blinds(s)

        # ===================================== #
        # END OF HELPER FUNCTIONS FOR APPLY_BET #
        # ===================================== #

        action_result = f"raised bet by {raise_size}."  # temp result string

        # last one standing in entire game!
        if len(s.players) == 1:
            action_result = "table won. last one standing."
            return action_result

        max_bet = max(s.bet_money)
        total_bet = s.bet_money[s.index_to_action] + raise_size
        is_all_in = raise_size == s.held_money[s.index_to_action]

        # check for: enough money condition, bet calls max_bet, bet raises with at least min raise (2x), is all-in
        if s.held_money[s.index_to_action] >= raise_size and (
            total_bet == max_bet or total_bet >= 2 * max_bet or is_all_in
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

        # WIN lOGIC POINT: ONLY ONE LEFT VYING FOR POT
        # check if only one player vying for pot and distribute. sidepots might still need to determine winners.
        no_pots_left = True
        for pot in s.pots:
            if len(pot.players) == 1 and pot.value > 0:
                # player wins pot
                pot_winning_player = pot.players[0]
                winning_index = s.players.index(pot_winning_player)
                s.held_money[winning_index] += pot.value
                pot.value = 0
            else:
                no_pots_left = False
        if no_pots_left:
            # start new hand of poker
            new_hands()
            action_result = "only one player left. new hands."
            return action_result

        # check if can move onto next betting round (meaning all people called max_bet, or folded, or hold no more money for all-ins)
        round_over = True
        for i in range(len(s.players)):
            if not (
                s.bet_money[i] == max_bet
                or s.bet_money[i] == -1
                or s.held_money[i] == 0
            ):
                round_over = False
                break

        # check for checking through from sb to action
        index_btn = (s.index_of_small_blind + len(s.players) - 1) % len(s.players)

        # all only checking or folds would end at button
        if s.index_to_action != index_btn:
            all_checks_or_folds = True
            for bet in s.bet_money:
                if not (bet == 0 or bet == -1):
                    # someone bet, not checked through
                    all_checks_or_folds = False
                    break
            # betting round is not over! all checks/folds
            if all_checks_or_folds:
                round_over = False

        # exception: big blind in preflop can raise/check (round not over)
        index_bb = (s.index_of_small_blind + 1) % len(s.players)
        next_to_action = (s.index_to_action + 1) % len(s.players)
        # big blind is next to action && in the preflop && bet amt equals game bb amt
        big_blind_can_check = (
            next_to_action == index_bb
            and len(s.community_cards) == 0
            and s.bet_money[index_bb] == s.big_blind
        )

        if not big_blind_can_check and round_over:
            # =================== #
            # start sidepot logic #
            # =================== #

            bet_size_indexes_dict: dict[int, list[int]] = {}
            for i, bet in enumerate(s.bet_money):
                if bet > 0:
                    bet_size_indexes_dict.setdefault(bet, []).append(i)

            # sort by smallest bet value ascending
            bet_size_indexes_tuples = list(
                zip(bet_size_indexes_dict.keys(), bet_size_indexes_dict.values())
            )
            bet_size_indexes_tuples.sort(key=lambda x: x[0])

            # for computing number of indexes
            prefix_sums = [0]
            sum = 0
            for i in bet_size_indexes_tuples:
                sum += len(bet_size_indexes_tuples[1])
                prefix_sums.append(sum)

            # only make sidepots if more than 1 bet_size. otherwise change nothing!
            if len(bet_size_indexes_tuples) > 1:
                # remove all current round bet sizings from main pot
                for tup in bet_size_indexes_tuples:
                    s.pots[0].value -= tup[0] * len(tup[1])

                # add smallest bet sizing for the pot of this sizing
                s.pots[0].value += bet_size_indexes_tuples[0][0] * prefix_sums[-1]

                for i, tup in enumerate(bet_size_indexes_tuples[1:]):
                    new_pot = copy.deepcopy(s.pots[0])
                    # value of new sidepot is difference between larger bet and smaller bet, * len(all) - len(poorer: i cuz prefix sums are +1)
                    new_pot.value = (tup[0] - bet_size_indexes_tuples[i - 1][0]) * (
                        prefix_sums[-1] - prefix_sums[i]
                    )
                    for poorer_player_index in bet_size_indexes_tuples[i - 1][1]:
                        new_pot.players.remove(s.players[poorer_player_index])
                    s.pots.insert(0, new_pot)

            # ================= #
            # end sidepot logic #
            # ================= #

            # resetting bet_money to 0, except for folded players
            for i in range(len(s.bet_money)):
                if s.bet_money[i] != -1:
                    s.bet_money[i] = 0

            # reveal new cards
            available_cards = Table.available_cards_shuffled(s)
            if len(s.community_cards) == 0:
                s.community_cards += available_cards[:3]
                new_round_set_index_to_action()
            elif len(s.community_cards) < 5:
                s.community_cards += available_cards[:1]
                new_round_set_index_to_action()
            else:
                # WIN LOGIC POINT: SHOWDOWN
                for pot in s.pots:
                    # showdown. determine winner by comparing hands. distribute pots.
                    pot_player_indexes = list(map(s.players.index, pot.players))
                    pot_player_hands: list[Hand] = []
                    for i in pot_player_indexes:
                        pot_player_hands.append(
                            Hand(s.community_cards + s.players_cards[i])
                        )

                    # tracks index of hand for players list
                    hand_index_tuples = list(zip(pot_player_hands, pot_player_indexes))
                    # sorts only by the hands desc (greatest first), not by the index
                    hand_index_tuples.sort(key=lambda x: x[0], reverse=True)

                    winners = [hand_index_tuples[0]]
                    for i, hand in enumerate(hand_index_tuples[1:]):
                        if winners[0][0] == hand[0]:
                            winners.append(hand_index_tuples[i])
                        else:
                            # early break because all hands that aren't equal will be less. cuz sorted
                            break

                    money_for_each = pot.value // len(winners)
                    for winner in winners:
                        s.held_money[winner[1]] += money_for_each

                    # distribute remainder from split pot to out-of-position players first (sb -> dealer/btn)
                    rem = pot.value % len(winners)
                    if rem > 0:
                        winners_indexes = [winner[1] for winner in winners]
                        farthest_index = s.index_of_small_blind
                        while rem > 0:
                            if farthest_index in winners_indexes:
                                s.held_money[farthest_index] += 1
                                rem -= 1
                            farthest_index = (farthest_index + 1) % len(s.players)

                new_hands()
                action_result = "best hand at showdown wins. new hands."
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
            held_money.append(DEFAULT_STARTING_STACK)
            bet_money.append(0)

        new_state = GameState(
            index_to_action=0,
            index_of_small_blind=0,
            players=team_ids,
            players_cards=players_cards,
            held_money=held_money,
            bet_money=bet_money,
            community_cards=[],
            pots=[main_pot],
            small_blind=DEFAULT_SB,
            big_blind=DEFAULT_BB,
        )

        Table.apply_blinds(new_state)

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
        update_json = {"game_state": state.model_dump_json()}
        db_client.table("tables").update(update_json).eq("id", table_id).execute()

    def __init__(self, table_id: str):
        self.table_id: str = table_id
        self.state: GameState = Table.read_state_from_db(table_id)

    async def make_move(self, raise_size: int | None = None):
        # human or bot move, default None for bot, float for human input

        result_str = ""

        if raise_size is not None:
            # human move
            result_str = Table.apply_bet(self.state, raise_size)
        else:
            # bot move
            res = await helpers.run_file(
                self.state.players[self.state.index_to_action], self.state
            )
            bot_raise_str = res.get("stdout")
            if bot_raise_str is not None:
                result_str = Table.apply_bet(self.state, int(bot_raise_str))
            else:
                raise ValueError

        # modify self.state based on the action
        Table.write_state_to_db(self.table_id, self.state)

        return result_str

    def get_visible_state(self):
        visible_state = copy.deepcopy(self.state)
        visible_state.players_cards.clear()
        return visible_state

    def multiply_blinds_by(self, n: int | None):
        if n is None:
            n = 2

        self.state.small_blind *= n
        self.state.big_blind *= n
        Table.write_state_to_db(self.table_id, self.state)
