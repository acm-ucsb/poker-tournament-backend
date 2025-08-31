from math import floor, ceil
from random import randint

from pydantic import BaseModel, Field

from src.core.broadcasting import BroadcastChannel
from src.core.card import Deck, Card, RANK, SUIT
from src.core.player import Player, PlayerData, ActionType
from src.core import update

class TableData(BaseModel):
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
        
        self.current_player: Player | None = None # makes it easier to keep track of players because 
            # folding removes players form the active player list
        self.last_player_to_raise: Player | None = None # small blind starts the betting round
        self.current_call: int = 0
        
        self.broadcaster = BroadcastChannel()
        
        self.pot: int = 0
    
    # TODO: refactor to only recompute when seating changes
    @property
    def players(self) -> list[Player]:
        return [player for player in self.seating if player]
    
    @property
    def size(self) -> int:
        return len(self.players)
    
    #TODO: refactor to only recompute when the button or seating changes
    @property
    def blinds(self) -> tuple[int, int]:
        """Gets the index of big blind and small blind
        Returns: A tuple of (small_blind, big_blind)
        """
        n = len(self.seating)
        small_blind = (self.button + 1) % n
        while self.seating[small_blind] == None:
            small_blind = (small_blind + 1) % n
        
        big_blind = (small_blind + 1) % n
        while self.seating[big_blind] == None:
            big_blind = (big_blind + 1) % n
        
        return (small_blind, big_blind)
    
    @property
    def small_blind(self) -> int:
        return self.blinds[0]
    
    @property
    def big_blind(self) -> int:
        return self.blinds[1]

    @property
    def data(self) -> TableData:
        return TableData(
            table_id=self.id,
            players=[player.data for player in self.players],
            seating=[seat.id if seat else None for seat in self.seating],
            current_player=self.current_player.id if self.current_player else "", # added as failsafe
            button=self.button,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            pot=self.pot,
            current_call=self.current_call,
            community_cards=[RANK[card.rank] + SUIT[card.suit] for card in self.community_cards]
        )
    
    def notify_broadcaster(self, update_code: update.UpdateCode, payload: update.BasePayload) -> None:
        self.broadcaster.update(self.data, update.UpdateData(code=update_code, payload=payload))
    
    def payout(self, winners: list[Player], paid = 0) -> int:
        """Distribute the pot to winners according to their contribution.
        Returns:
            int: The amount paid to all the winners.
        """
        # precondition: winners are sorted by ascending contribution
        winners.sort(key=lambda player: player.contribution)
        total_paid = paid
        has_indivisible = False
        
        n = len(winners)
        for i, winner in enumerate(winners):
            eligible_amount = sum([min(winner.contribution, player.contribution) for player in self.players])
            payout = max(min(eligible_amount - total_paid, self.pot) / (n - i), 0)
            
            if ceil(payout) > payout:
                has_indivisible = True
                
            if has_indivisible and n - i == 1:
                payout -= 1
                
            payout = floor(payout)
                
            total_paid += payout
            self.pot -= payout
            winner.chips += payout
        
        # give the indivisible chip to first winner to the left of the button
        if has_indivisible:
            target = (self.button + 1) % len(self.seating)
            while self.seating[target] == None or self.seating[target] not in winners:
                target = (target + 1) % len(self.seating)
                
            self.seating[target].chips += 1
            total_paid += 1

        return total_paid - paid
    
    def start_hand(self):
        # resetting everything
        self.deck.reset()
        self.community_cards.clear()
        self.pot = 0
        
        for player in self.players:
            player.new_hand()
            
        # deal cards to players
        # TODO: check how to deal cards to players?
        for _ in range(2):
            for player in self.players:
                player.hand.append(self.deck.deal_card())
        
        # force blinds to post
        blinds_idx = self.blinds
        sb, bb = self.seating[blinds_idx[0]], self.seating[blinds_idx[1]]
        sb_amount, bb_amount = self.blind_amount
        
        self.pot += sb.force_bet(sb_amount)
        self.pot += bb.force_bet(bb_amount)
        
        self.current_call = bb_amount
        
        # skip bb and sm since there were forced to bet
        self.current_player = self.players[(self.players.index(bb) + 1) % len(self.players)]
        self.last_player_to_raise = bb
    
    # clean up after the last round
    def end_hand(self):
        # TODO: determine the winner
        strengths = [(player, self.deck.hand_strength(player.hand + self.community_cards)) \
                    for player in self.players if  not player.has_folded]
        
        strengths.sort(key=lambda x: x[1], reverse=True)
        highest_strength = strengths[0][1]
        winners = [player for player, strength in strengths if strength == highest_strength]    
        # payout the winners
        _ = self.payout(winners)
        # TODO: determine if player gets eliminated and notify matchmaking
        for player in self.seating:
            if player == None:
                continue
            if player.chips == 0:
                player.is_eliminated = True
                # remove player from table
                self.seating[self.seating.index(player)] = None
                # TODO: notify matchmaking and broadcast channel
            else: # reset player state
                player.has_folded = False
                player.contribution = 0
                player.hand = []
                
        # TODO : notify matchmaking of eliminated players from "master" matchmaking object 
            # assuming matchmaking object is the one that created this table 
            #   -> some static variable in Table class for callback?


        # move the button
        self.button = (self.button + 1) % len(self.seating)
        while self.seating[self.button] == None:
            self.button = (self.button + 1) % len(self.seating)

        self.current_player = self.seating[self.button]
    
    #TODO: test
    def step(self):
        self.start_hand()
        self.step.active_players = self.players
        
        # all players in at this point, so don't have to check for folded players
        start = self.step.active_players.index(self.current_player) # rounds start from small blind
        # flop starts from after big blind
        after_big = (self.step.active_players.index(self.current_player) + 2) % len(self.step.active_players)
        """
        each betting round starts from first active player starting from little blind 
        to check if betting has ended:
            if current player is last player to raise and all other active players have called:
        if only one active player remains, end the hand
        need a raise variable to check how much to call
        """
        # blinds
        self.betting_round(self.step.active_players, after_big)
        # only one player remaining
        if len([player for player in self.step.active_players if not player.has_folded]) == 1:
            self.end_hand()
            return
        
        # flop
        _ = self.deck.deal_card() # burn
        self.community_cards.extend([self.deck.deal_card() for _ in range(3)])
        while self.step.active_players[start].has_folded:
            start = (start + 1) % len(self.step.active_players) # next active player past small blind
        
        self.last_player_to_raise = self.step.active_players[start] # reset to small blind in case of all checks
        self.betting_round(self.step.active_players, start) # start from first active player from small blind
        if len([player for player in self.step.active_players if not player.has_folded]) == 1:
            self.end_hand()
            return
        
        # turn
        _ = self.deck.deal_card() # burn
        self.community_cards.append(self.deck.deal_card())
        while self.step.active_players[start].has_folded:
            start = (start + 1) % len(self.step.active_players) # next active player past small blind
        
        self.last_player_to_raise = self.step.active_players[start] # reset to small blind in case of all checks
        self.betting_round(self.step.active_players, start)
        if len([player for player in self.step.active_players if not player.has_folded]) == 1:
            self.end_hand()
            return
        
        #river
        _ = self.deck.deal_card() # burn
        self.community_cards.append(self.deck.deal_card())
        while self.step.active_players[start].has_folded:
            start = (start + 1) % len(self.step.active_players) # next active player past small blind
        
        self.last_player_to_raise = self.step.active_players[start] # reset to small blind in case of all checks
        self.betting_round(self.step.active_players, start)
        
        self.end_hand()
        return
        
        
        
    #TODO: test
    # handles the betting round logic
    def betting_round(self, players: list[Player], start) -> None:
        current_player = start
        ended = False
        while True:
            for player in players:
                if player.has_folded: # folded
                    current_player = (current_player + 1) % len(players)
                    self.current_player = players[current_player]
                    continue
                action = player.act()
                match action.action:
                    case ActionType.CHECK:
                        if self.current_call > player.contribution:
                            # cannot check when there's an outstanding bet
                            raise ValueError("Cannot check when there's an outstanding bet")
                    case ActionType.CALL:
                        self.pot += action.amount
                        if not self.last_player_to_raise:
                            self.last_player_to_raise = player # allows big blind to raise pre-flop
                    case ActionType.FOLD:
                        player.has_folded = True
                        # lazy deletion to make index tracking easier
                    case ActionType.RAISE:
                        self.pot += action.amount
                        self.current_call = player.contribution
                        self.last_player_to_raise = player
                        # betting reopens for all other active players
                current_player = (current_player + 1) % len(players)
                self.current_player = players[current_player]

                if self.current_player == self.last_player_to_raise:
                    ended = True
                    break # betting round is over
                if sum([1 for p in players if p.has_folded]) == len(players) - 1: # only one player remains
                    ended = True
                    break
            if ended:
                break
            
    
    
    def close(self):
        # close all broadcasting channels and clean up any remaining resources
        ...
    
    def get_vacant(self) -> list[int]:
        """Calculate all vacant seating values based on how far they are from being a BB
        Returns:
            A list of all vacant index, sorted by seating value
        """
        start = self.big_blind
        vacant = []
        n = len(self.seating)
        for i in range(start, n + start):
            if self.seating[i % n] == None:
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
        self.seating[(selected)] = None # need to change to None, not remove altogether
        
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