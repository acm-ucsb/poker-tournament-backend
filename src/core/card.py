from random import randint

from pydantic import BaseModel, Field

SUIT = {
    1: "S",
    2: "H",
    3: "D",
    4: "C",
}

RANK = {
    13: "A",
    12: "K",
    11: "Q",
    10: "J",
    9: "10",
    8: "9",
    7: "8",
    6: "7",
    5: "6",
    4: "5",
    3: "4",
    2: "3",
    1: "2",
}

class Card(BaseModel):
    rank: int = Field(..., ge=1, le=13)
    suit: int = Field(..., ge=1, le=4)
    
class Deck():
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        self.used_card: list[int] = [0] * 52
        
    def deal_card(self) -> Card:
        if sum(self.used_card) == 52:
            raise Exception("No more card left to deal")
        
        card = None
        while card == None or self.used_card[card] == 1:
            rank = randint(1, 13)
            suit = randint(1, 4)
            card = suit * 4 + rank
        
        self.used_card[card] = 1
            
        return Card(rank=card[0], suit=card[1])
