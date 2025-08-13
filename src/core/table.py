from random import randint

from src.core.card import Deck, Card
from src.core.player import Player

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
        
    @property
    def players(self) -> list[Player]:
        return [player for player in self.seating if player]
    
    @property
    def size(self) -> int:
        return len(self.players)
    
    @property
    def blinds(self) -> tuple[int, int]:
        """Gets the index of big blind and small blind
        Returns: A tuple of (small_blind, big_blind)
        """
        n = len(self.seating)
        small_blind = (self.button + 1) % n
        while self.seating[small_blind] == None:
            small_blind = (small_blind + 1) % n
        
        big_blind = (self.button + 1) % n
        while self.seating[big_blind] == None:
            big_blind = (big_blind + 1) % n
        
        return (small_blind, big_blind)
    
    @property
    def small_blind(self) -> int:
        return self.blinds[0]
    
    @property
    def big_blind(self) -> int:
        return self.blinds[1]
    
    def start_hand(self):
        # resetting everything
        self.deck.reset()
        self.community_cards.clear()
        # TODO: reset pot
        
        for player in self.players:
            player.new_hand()
            
        # deal cards to players
        # TODO: check how to deal cards to players?
        for _ in range(2):
            for player in self.players:
                player.hand.append(self.deck.deal_card())
        
        # TODO: force blinds to post
    
    # clean up after the last round
    def end_hand(self):
        # TODO: determine the winner
        # TODO: distribute pot
        # TODO: determine if player gets eliminated and notify matchmaking
        
        # move the button
        self.button = (self.button + 1) % len(self.seating)
        while self.seating[self.button] == None:
            self.button = (self.button + 1) % len(self.seating)
    
    def close(self):
        # close all broadcasting channels and clean up any remaining resources
        ...
    
    # TODO: test
    def get_vacant(self) -> list[int]:
        """Calculate all vacant seating values based on how far they are from being a BB
        Returns:
            A list of all vacant index, sorted by seating value
        """
        start = self.big_blind
        vacant = []
        n = len(self.seating)
        for i in range(start, n + start):
            if self.seating[i % n] != None:
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
    
    # TODO: test
    def remove_random_player(self) -> Player:
        """
        Raises:
            IndexError: Raise if no more players are left
        """
        if self.size == 0:
            raise IndexError("No more player left to remove")
        
        players = self.players
        selected = players[randint(0, len(players))]
        self.seating.remove(selected)
        
        return selected
    
    # TODO: test
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