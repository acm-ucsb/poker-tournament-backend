from .player import Player
from .signaling import EventNotifier

from typing import Sequence

class Table(EventNotifier):
    """
    Attributes:
        players: a array of Player object assigned to a table
    """
    def __init__(self, table_id: str):
        self.id: str = table_id
        self.players: list[Player] = []
        super().__init__()
    
    def __del__(self):
        pass
    
    def close(self):
        # close all broadcasting channels and clean up any remaining resources
        pass
    
    def add_player(self, player: Player) -> None:
        self.players.append(player)
    
    def add_players(self, players: list[Player]) -> None:
        self.players.extend(players)
    
    @property
    def size(self) -> int:
        return len(self.players)
    
    def remove_random_players(self, n: int) -> list[Player]:
        selected_players, self.players = self.players[:n], self.players[n:]
        return selected_players
        
    def remove_all_players(self) -> list[Player]:
        players = [player for player in self.players]
        self.players = []
        return players