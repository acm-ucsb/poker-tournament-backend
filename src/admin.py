from fastapi import Depends, APIRouter, HTTPException, status
from gotrue import User
from postgrest import APIError
from src.util.models import unauth_res, SubmittedFile, FileRunResult, GameState
from src.util.auth import verify_admin_user
from src.util.supabase_client import db_client
import src.util.helpers as helpers
from src.core.table import Table
from src.core.tournament import tournament

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/test/", response_model=str)
def is_admin(_: User = Depends(verify_admin_user)):
    return "user is admin. would raise exception otherwise."


@admin_router.get("/submission/", response_model=SubmittedFile, responses=unauth_res)
async def get_submission_by_team_id(team_id: str, _: User = Depends(verify_admin_user)):
    # team_id is not guaranteed to exist!
    try:
        table_res = (
            db_client.table("teams")
            .select("has_submitted_code")
            .eq("id", team_id)
            .single()
            .execute()
        )

        if table_res.data["has_submitted_code"]:
            result = await helpers.get_file_with_stem(team_id)

            if result:
                filename, content = result
                return {"filename": filename, "content": content}
            else:
                # set team.has_submitted_code to false, submitted code cannot be found
                db_client.table("teams").update({"has_submitted_code": False}).eq(
                    "id", team_id
                ).execute()

    except APIError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="team_id is invalid",
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@admin_router.post(
    "/submission/run/", response_model=FileRunResult, responses=unauth_res
)
async def run_code_by_team_id(
    team_id: str, state: GameState, _: User = Depends(verify_admin_user)
):
    return await helpers.run_file(team_id, state)


@admin_router.get("/tables/{table_id}/", response_model=GameState, responses=unauth_res)
def read_full_gamestate(table_id: str, _: User = Depends(verify_admin_user)):
    return Table.read_state_from_db(table_id)


@admin_router.post("/tables/create/", responses=unauth_res)
def create_tables():
    tournament.insert_tables()
    return "success"


@admin_router.delete("/tables/delete/", responses=unauth_res)
def delete_tables(_: User = Depends(verify_admin_user)):
    tournament.delete_tables()
    return "success"


@admin_router.post(
    "/tables/move/",
    response_model=list[str],
    responses=unauth_res,
    description="table_ids for specifying which tables to make one move on with bots (default all).",
)
async def make_move_on_tables(
    table_ids: list[str] | None = None, _: User = Depends(verify_admin_user)
):
    return await tournament.make_moves(table_ids)


@admin_router.post(
    "/tables/{table_id}/move/",
    response_model=list[str],
    responses=unauth_res,
    description="for human input",
)
async def make_move_on_table(
    table_id: str, raise_size: float, _: User = Depends(verify_admin_user)
):
    return await tournament.make_moves([table_id], [raise_size])
