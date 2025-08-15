from enum import Enum
from typing import Optional

from pydantic import BaseModel
from src.core.card import Card

class ActionType(Enum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    BET = 3
    RAISE = 4

class Action(BaseModel):
    action: ActionType
    amount: Optional[int] = None

class Player:
    def __init__(self, player_id: str, starting_chips: int = 0):
        self.id: str = player_id
        self.chips: int = starting_chips
        
        self.hand: list[Card] = []
        
        self.is_eliminated: bool = False
        self.has_folded: bool = False
        
        self.contribution: int = 0
    
    @property
    def is_all_in(self):
        return self.chips == 0
    
    def new_hand(self):
        self.hand = []
        self.is_all_in = False
        self.has_folded = False
        self.contribution = 0
        
    def act(self) -> Action:
        ...
        
    def force_bet(self, amount: int) -> int:
        """Force player to bet `amount`, if not possible player goes all in.
        Returns: Amount player actually contributed.
        """
        if amount >= self.chips:
            contribution = self.chips
            self.chips = 0
            self.contribution += contribution
            return contribution
        
        self.chips -= amount
        self.contribution += amount
        return amount