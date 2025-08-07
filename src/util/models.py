from pydantic import BaseModel, Field
from typing import Any
from fastapi import status


class ErrorResponse(BaseModel):
    detail: str


unauth_res: dict[int | str, dict[str, str | Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "detail": "not authenticated",
    }
}

no_content_res: dict[int | str, dict[str, str | Any]] = {status.HTTP_204_NO_CONTENT: {}}


class SubmittedFile(BaseModel):
    filename: str
    content: str


class Card(BaseModel):
    rank: int = Field(..., ge=1, le=13)
    suit: int = Field(..., ge=1, le=4)


class GameState(BaseModel):
    community_cards: list[Card]
    num_players: int
    current_round: int
    players: list[int]
    action_on: int
