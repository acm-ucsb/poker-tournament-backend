from pydantic import BaseModel, Field
from typing import Any
from fastapi import status


class ErrorResponse(BaseModel):
    detail: str


auth_required_responses: dict[int | str, dict[str, str | Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "detail": "Not authenticated",
    }
}


class Card(BaseModel):
    rank: int = Field(..., ge=1, le=13)
    suit: int = Field(..., ge=1, le=4)


class GameState(BaseModel):
    community_cards: list[Card]
    num_players: int
    current_round: int
    players: list[int]
    action_on: int
