from random import randint
from pydantic import BaseModel, Field

SUIT = {
    0: "S",
    1: "H",
    2: "D",
    3: "C",
}

RANK = {
    12: "A",
    11: "K",
    10: "Q",
    9: "J",
    8: "10",
    7: "9",
    6: "8",
    5: "7",
    4: "6",
    3: "5",
    2: "4",
    1: "3",
    0: "2",
}


class Card(BaseModel):
    rank: int = Field(..., ge=0, le=12)
    suit: int = Field(..., ge=0, le=3)

    def __str__(self) -> str:
        return f"{RANK[self.rank]}{SUIT[self.suit]}"


class Deck:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.used_card: list[int] = [0] * 52

    def deal_card(self) -> Card:
        if sum(self.used_card) == 52:
            raise Exception("No more card left to deal")

        card = None
        while card == None or self.used_card[card] == 1:
            rank = randint(0, 12)
            suit = randint(0, 3)
            card = suit * 13 + rank

        self.used_card[card] = 1

        return Card(rank=rank, suit=suit)
