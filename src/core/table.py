from random import randint

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
    ):
        self.id: str = table_id
        self.seating: list[Player | None] = [None] * max_table_size
        self.min_table_size = min_table_size
        
    @property
    def players(self) -> list[Player]:
        return [player for player in self.seating if player]
    
    @property
    def size(self) -> int:
        return len(self.players)
    
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