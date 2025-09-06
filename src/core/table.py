from __future__ import annotations

from typing import TYPE_CHECKING
from math import floor, ceil
from random import randint

from pydantic import BaseModel, Field
""" UNCOMMENT EVERYTHING TO DO WITH BROADCASTING WHEN NEEDED """
# from src.core.broadcasting import BroadcastChannel, UpdateData UNCOMMENT LATER
from src.core.card import Deck, RANK, SUIT
from src.core.player import ActionType

if TYPE_CHECKING:
    from src.core.broadcasting import BasePayload
    from src.core.card import Card
    from src.core.player import Player, PlayerData


class TableState(BaseModel):
    table_id: str = Field(serialization_alias="table-id")
    players: list[PlayerData]
    seating: list[str | None]
    current_player: str = Field(serialization_alias="current-player")

    button: int
    small_blind: int = Field(serialization_alias="small-blind")
    big_blind: int = Field(serialization_alias="big-blind")

    pot: int
    current_call: int = Field(serialization_alias="call-amount")
    community_cards: list[str] = Field(serialization_alias="community-card")


class Table:
    """
    Notes:
        Always call `table.close()` before removing a table.
    """

    def __init__(
        self,
        table_id: str,
        max_table_size: int = 8,
        min_table_size: int = 5,
        initial_bind_amount: tuple[int, int] = (10, 30),
    ):
        self.id: str = table_id
        self.seating: list[Player | None] = [None] * max_table_size
        self.min_table_size = min_table_size

        self.deck = Deck()
        self.community_cards: list[Card] = []

        self.blind_amount: tuple[int, int] = initial_bind_amount
        self.button: int = 0

        self.current_player: Player | None = (
            None  # makes it easier to keep track of players because
        )
        # folding removes players form the active player list
        self.last_player_to_raise: Player | None = (
            None  # small blind starts the betting round
        )
        self.current_call: int = 0

         # self.broadcaster = BroadcastChannel() UNCOMMENT LATER

        self.pot: int = 0

    # TODO: refactor to only recompute when seating changes
    @property
    def players(self) -> list[Player]:
        return [player for player in self.seating if player]

    @property
    def max_size(self) -> int:
        """Compute the amount of seating at the table."""
        return len(self.seating)

    @property
    def size(self) -> int:
        """Compute the amount of players at the table."""
        return len(self.players)

    # TODO: refactor to only recompute when the button or seating changes
    @property
    def blinds(self) -> tuple[int, int]:
        """Gets the index of big blind and small blind
        Returns: A tuple of (small_blind, big_blind)
        """
        n = len(self.seating)
        small_blind = (self.button + 1) % n
        while self.seating[small_blind] is None:
            small_blind = (small_blind + 1) % n

        big_blind = (small_blind + 1) % n
        while self.seating[big_blind] is None:
            big_blind = (big_blind + 1) % n

        return (small_blind, big_blind)

    @property
    def small_blind(self) -> int:
        return self.blinds[0]

    @property
    def big_blind(self) -> int:
        return self.blinds[1]

    @property
    def state(self) -> TableState:
        return TableState(
            table_id=self.id,
            players=[player.data for player in self.players],
            seating=[seat.id if seat else None for seat in self.seating],
            current_player=self.current_player.id
            if self.current_player
            else "",  # added as failsafe
            button=self.button,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            pot=self.pot,
            current_call=self.current_call,
            community_cards=[
                RANK[card.rank] + SUIT[card.suit] for card in self.community_cards
            ],
        )
    """ Used for testing """
    def __str__(self) -> str:
        s = f"\nTable {self.id}: \n"
        for player in self.seating:
            if player is not None:
                s += f"{(player.id, 
                         player.chips, 
                         player.contribution,
                         [str(card) for card in player.hand], 
                         'I' if not player.has_folded else 'F')}, "
        s += "\n"
        s += f"Community Cards: {[str(card) for card in self.community_cards]}\n"
        s += f"Action: {self.current_player.id if self.current_player else 'None'}\n"
        s += f"Last to Raise: {self.last_player_to_raise.id if self.last_player_to_raise else 'None'}\n"
        s += f"Pot: {self.pot}\n"
        s += f"Current Call: {self.current_call}\n"

        return s

    # TODO: test
    def payout(self) -> list[tuple[Player, int]]:
        """
        Returns: a list describing how much a player was paid
        """
        hands = [
            (rank, [card.rank for card in cards], player)
            for rank, cards, player in [
                (*player.build_best_hand(self.community_cards), player)
                for player in self.players
                if not player.has_folded
            ]
        ]

        paid = 0
        players_paid = []
        while self.pot > 0:
            winners = self._eval_winners(hands)
            # non-folded losers
            hands = [hand for hand in hands if hand[2] not in winners]
            current_paid, current_player_paid = self.payout_helper(winners, paid)
            paid += current_paid
            players_paid.extend(current_player_paid)
            
        return players_paid

    def payout_helper(self, winners: list[Player], paid=0) -> tuple[int, list[tuple[Player, int]]]:
        """Distribute the pot to winners according to their contribution.
        Returns:
            - The total amount paid to all the winners.
            - A list of all players paid and the amount paid.
        """
        winners = sorted(winners, key=lambda player: player.contribution)
        total_paid = paid
        has_indivisible = False
        players_paid: list[tuple[Player, int]] = []

        n = len(winners)
        for i, winner in enumerate(winners):
            eligible_amount = sum(
                [
                    min(winner.contribution, player.contribution)
                    for player in self.players
                ]
            )
            payout = max(min(eligible_amount - total_paid, self.pot) / (n - i), 0)
            if ceil(payout) > payout:
                has_indivisible = True

            if has_indivisible and n - i == 1:
                payout -= 1

            payout = floor(payout)

            total_paid += payout
            self.pot -= payout
            winner.chips += payout
            players_paid.append((winner, payout))

        # give the indivisible chip to first winner to the left of the button
        if has_indivisible:
            target = (self.button + 1) % len(self.seating)
            while self.seating[target] is None or self.seating[target] not in winners:
                target = (target + 1) % len(self.seating)

            self.seating[target].chips += 1
            total_paid += 1

        return (total_paid - paid, players_paid)

    # TODO: test
    def eval_winners(self, hands: list[tuple[int, list[int], Player]]) -> list[Player]:
        def eval_tie_break(hand_1: list[Card], hand_2: list[Card]) -> int:
            for card_1, card_2 in zip(hand_1, hand_2):
                if card_1 > card_2:
                    return -1
                if card_1 < card_2:
                    return 1

            return 0

        best_rank = max([rank for rank, _, _ in hands])
        best_hands = [
            (hand, player) for rank, hand, player in hands if rank == best_rank
        ]
        winners = [best_hands[0][1]]
        current_hand = best_hands[0][0]
        for hand, player in best_hands[1:]:
            match eval_tie_break(current_hand, hand):
                case 0:
                    winners.append(player)
                case 1:
                    current_hand = hand
                    winners = [player]
                case -1:
                    pass

        return winners

    def start_hand(self) -> None:
        # resetting everything
        self.deck.reset()
        self.community_cards.clear()
        self.pot = 0

        for player in self.players:
            player.new_hand()
        
        self.broadcaster.update(broadcasting.NewHandPayload())

        # deal cards to players
        # NOTE: maybe deal starting from the button?
        cards_dealt = []
        for player in self.players:
            for _ in range(2):
                dealt_card = self.deck.deal_card()
                cards_dealt.append(dealt_card)
                player.hand.append(self.deck.deal_card())
            cards_dealt = []
            self.broadcaster.update(broadcasting.HandDealtPayload(player_id=player.id, cards=cards_dealt))

        # force blinds to post
        blinds_idx = self.blinds
        sb, bb = self.seating[blinds_idx[0]], self.seating[blinds_idx[1]]
        sb_amount, bb_amount = self.blind_amount

        self.pot += sb.force_bet(sb_amount)
        self.pot += bb.force_bet(bb_amount)

        self.broadcaster.update(broadcasting.PlayerActedPayload(player_id=sb.id, action="CALL" if not sb.is_all_in else "ALL-IN", amount=sb.contribution))
        self.broadcaster.update(broadcasting.PlayerActedPayload(player_id=bb.id, action="CALL" if not bb.is_all_in else "ALL-IN", amount=bb.contribution))

        self.current_call = bb_amount

        # skip bb and sb since there were forced to bet
        self.current_player = self.players[
            (self.players.index(bb) + 1) % len(self.players)
        ]
        self.last_player_to_raise = None

    # clean up after the last round
    def end_hand(self):
        self.broadcaster.update(broadcasting.ShowdownPayload())
        winners = self.payout()
        self.broadcaster.update(broadcasting.PayoutPayload(payouts=[broadcasting.Payout(player_id=player.id, amount=payout) for player, payout in winners]))
        
        for idx, player in enumerate(self.seating):
            if player is None:
                continue
            if player.chips == 0:
                player.is_eliminated = True
                self.seating[idx] = None
                self.broadcaster.update(broadcasting.PlayerEliminatedPayload(player_id=player.id))

        # TODO : notify matchmaking of eliminated players from "master" matchmaking object
        # assuming matchmaking object is the one that created this table
        #   -> some static variable in Table class for callback?
        
        # move the button
        self.button = (self.button + 1) % len(self.seating)
        while self.seating[self.button] is None:
            self.button = (self.button + 1) % len(self.seating)
            
        self.broadcaster.update(broadcasting.ButtonMovedPayload(button_seat=self.button, big_blind_seat=self.big_blind, small_blind_seat=self.small_blind))

        # self.current_player = self.seating[self.button] # NOTE: prlb don't need this?

    def start_betting_round(self, current_round: int, active_players: list[Player]) -> tuple[list[Player], int]:
        """
        Args:
            round: [0-2]
                - 0: flop
                - 1: turn
                - 2: river
        Returns:
            - A list of active players
            - The starting player index
        """
        
        cards_deal_mapping = [3, 1, 1]
        cards_dealt = []
        
        for _ in range(cards_deal_mapping[current_round]):
            self.deck.deal_card() # burn
            dealt_card = self.deck.deal_card()
            self.community_cards.append(dealt_card)
            cards_dealt.append(dealt_card)
        
        self.broadcaster.update(broadcasting.CCDealtPayload(cards=cards_dealt))
        
        active_players = [player for player in active_players if not player.has_folded]
        
        # next active player past button
        idx = (self.button + 1) % self.max_size
        current_player = self.seating[idx]
        while current_player is None or current_player.has_folded:
            idx = (idx + 1) % self.max_size
            current_player = self.seating[idx]
        
        current_player_idx = active_players.index(current_player)
        
        return (active_players, current_player_idx)

    # TODO: test
    def run(self):
        """
        - Each betting round starts from left most active player from the button.
        - If current player is last player to raise and all other active players have called:
            - if only one active player remains, end the hand
            - need a raise variable to check how much to call
        """
        self.start_hand()
        
        # pre-flop
        current_player_idx = self.players.index(self.current_player)
        active_players = self.players.copy()
        
        self.run_betting_round(active_players, current_player_idx)
        
        if len([player for player in active_players if not player.has_folded]) == 1:
            self.end_hand()
            return

        # flop, turn, river
        for current_round in range(3):
            active_players, current_player_idx = self.start_betting_round(current_round, active_players)
            self.run_betting_round(active_players, current_player_idx)
            if len([player for player in active_players if not player.has_folded]) == 1:
                break

        self.end_hand()

    # handles the betting round logic
    def run_betting_round(self, active_players: list[Player], starting_player_idx: int) -> None:
        current_player_idx = starting_player_idx
        ended = False
        while not ended:
            for player in active_players:
                if player.has_folded:
                    current_player_idx = (current_player_idx + 1) % len(active_players)
                    self.current_player = active_players[current_player_idx]
                    continue
                
                action = player.act(self.state)
                match action.action:
                    case ActionType.CHECK:
                        self.broadcaster.update(broadcasting.PlayerActedPayload(action="CHECK", amount=0))

                    case ActionType.CALL:
                        self.pot += action.amount
                        self.broadcaster.update(broadcasting.PlayerActedPayload(action="CALL", amount=action.amount))
                        if player.is_all_in:
                            self.broadcaster.update(broadcasting.PlayerActedPayload(action="ALL-IN", amount=0))
                        
                        # NOTE: not sure if we need this?
                        if self.last_player_to_raise is None:
                            self.last_player_to_raise = (
                                player  # allows big blind to raise pre-flop
                            )
                    case ActionType.FOLD:
                        self.broadcaster.update(broadcasting.PlayerActedPayload(action="FOLD", amount=0))
                        # lazy deletion to make index tracking easier
                    case ActionType.RAISE:
                        self.pot += action.amount
                        self.current_call = player.contribution
                        self.last_player_to_raise = player
                        self.broadcaster.update(broadcasting.PlayerActedPayload(action="RAISE", amount=action.amount))
                        if player.is_all_in:
                            self.broadcaster.update(broadcasting.PlayerActedPayload(action="ALL-IN", amount=0))
                        # betting reopens for all other active players
                        
                current_player_idx = (current_player_idx + 1) % len(active_players)
                self.current_player = active_players[current_player_idx]

                if self.current_player == self.last_player_to_raise:
                    ended = True
                    break
                if len([player for player in active_players if not player.has_folded]) == 1:
                    ended = True
                    break

    def close(self):
        # close all broadcasting channels and clean up any remaining resources
        self.broadcaster.update(broadcasting.TableClosedPayload())
        self.broadcaster.disconnect_all()

    def get_vacant(self) -> list[int]:
        """Calculate all vacant seating values based on how far they are from being a BB
        Returns:
            A list of all vacant index, sorted by seating value
        """
        start = self.big_blind
        vacant = []
        n = len(self.seating)
        for i in range(start, n + start):
            if self.seating[i % n] is None:
                vacant.append(i % n)

        return vacant[::-1]

    # TODO: test
    def add_player(self, player: Player) -> None:
        """Adds player in the most valuable seat
        Raises:
            BufferError: Raised where there's not enough table space
        """
        vacant = self.get_vacant()

        if len(vacant) < 1:
            raise BufferError("Not enough space to allocate another player")

        self.seating[vacant[0]] = player

    # TODO: test
    def add_players(self, players: list[Player]) -> None:
        """Adds players in the most valuable seat, priority given to descending order of `players`
        Raises:
            BufferError: Raised where there's not enough table space
        """
        vacant = self.get_vacant()

        if len(vacant) < len(players):
            raise BufferError("Not enough space to allocate another player")

        for player, seat in zip(players, vacant):
            self.seating[seat] = player

    def remove_random_player(self) -> Player:
        """
        Raises:
            IndexError: Raise if no more players are left
        """
        if self.size == 0:
            raise IndexError("No more player left to remove")

        players = self.players
        selected = randint(0, len(players))
        player = players[selected]
        self.seating[(selected)] = None  # need to change to None, not remove altogether

        return player

    def remove_random_players(self, n: int) -> list[Player]:
        """
        Args:
            n: Number of players to remove
        Raises:
            IndexError: Raise if n > table.size
        """
        if n > self.size:
            raise IndexError("Trying to remove too many players from table")

        return [self.remove_random_player() for _ in range(n)]

    def remove_all_players(self) -> list[Player]:
        players = [player for player in self.seating]
        self.seating = []
        return players
