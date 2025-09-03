from pydantic import BaseModel
from typing import Any, TypedDict
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


# class Card(BaseModel):
#     repr: str
#     rank: int = Field(..., ge=1, le=13)
#     suit: int = Field(..., ge=1, le=4)


class Pot(BaseModel):
    value: float
    players: list[str]


# cards are defined as 1st char: A(2-9)TJQK, 2nd char: SDCH
# currently does not take into account side pots
class GameState(BaseModel):
    players: list[str]  # team_ids
    players_cards: list[list[str]]
    held_money: list[float]
    bet_money: list[float]  # per round, -1 for fold, 0 for check/hasn't bet yet
    community_cards: list[str]
    pots: list[Pot]
    current_round: str  # preflop, flop, turn, river


class FileRunResult(TypedDict):
    status: str
    stdout: str | None
    stderr: str | None
    message: str
