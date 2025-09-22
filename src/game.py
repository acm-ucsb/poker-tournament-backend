from fastapi import Depends
from gotrue import User
from fastapi import APIRouter
from src.util.models import unauth_res, GameState
from src.util.auth import verify_user
from src.core.table import Table

game_router = APIRouter(prefix="/game", tags=["game"])


@game_router.get(
    "/{table_id}/",
    response_model=GameState,
    description="for global table view without peeking player cards. players_cards is an empty array",
)
def get_visible_state(table_id: str):
    return Table(table_id).get_visible_state()


@game_router.post(
    "/move/",
    responses=unauth_res,
    description="for human users to play??? not implemented yet",
)
def make_move(user: User = Depends(verify_user)):
    pass
