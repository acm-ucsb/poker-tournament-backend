from src.core.card import Card

class Player:
    def __init__(self, player_id: str, starting_chips: int = 0):
        self.id: str = player_id
        self.chips: int = starting_chips
        
        self.hand: list[Card] = []
        
        self.is_all_in: bool = False
        self.has_folded: bool = False
        
        self.contribution: int = 0          # chips in current betting round
        self.total_contributed: int = 0     # chips contributed in whole hand
        
    @property
    def is_eliminated(self):
        return self.chips <= 0
    
    def new_hand(self):
        self.hand = []
        self.is_all_in = False
        self.has_folded = False
        self.contribution = 0
    
    def new_round(self):
        self.new_hand()
        self.total_contributed = 0