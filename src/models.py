from pydantic import BaseModel, Field


class Card(BaseModel):
    rank: int = Field(..., ge=1, le=13)
    suit: int = Field(..., ge=1, le=4)


class GameState(BaseModel):
    community_cards: list[Card]
    num_players: int
    current_round: int
    players: list[int]
    action_on: int
