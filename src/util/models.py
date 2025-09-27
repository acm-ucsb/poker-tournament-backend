from pydantic import BaseModel
from typing import Any, TypedDict, NotRequired
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


class Pot(BaseModel):
    value: float  # money in pot
    players: list[str]  # players vying for this pot, team_ids


# cards are defined as 1st char: a(2-9)tjqk, 2nd char: sdch
class GameState(BaseModel):
    players: list[str]  # team_ids
    players_cards: list[list[str]]  # list of two card strs per team by index
    held_money: list[float]  # money per team by index
    bet_money: list[float]  # per round by index, -1 for fold, 0 for check/hasn't bet
    community_cards: list[str]
    pots: list[Pot]  # list for the case of sidepots
    current_round: str  # for convenience: preflop, flop, turn, river


class FileRunResult(TypedDict):
    status: str
    stdout: NotRequired[str]
    stderr: NotRequired[str]
    message: str


class AdminUpdate(BaseModel):
    player_id: str
    move: str # FOLD, CHECK, CALL, RAISE
    amount: int | None
    table_id: str