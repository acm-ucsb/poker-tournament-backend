from fastapi import Depends, APIRouter, HTTPException, status
from gotrue import User
from postgrest import APIError
from src.util.models import unauth_res, SubmittedFile, FileRunResult, GameState, AdminUpdate
from src.util.auth import verify_admin_user
from src.util.supabase_client import db_client
import src.util.helpers as helpers

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# endpoint for admins to update the game state
@admin_router.post("/update/", response_model=AdminUpdate)
def update_game(updates: AdminUpdate):
    try:
        current, count = db_client.table("tables") \
            .select("game_state") \
            .eq("id", updates.table_id) \
            .execute()
    except Exception as e:
        print("No game state to retrieve")

    state = current[1]

    player_index = state["players"].index(updates.player_id)

    move_type = updates.move
    if move_type == "FOLD":
        state["bet_money"][player_index] = -1
    # either way raising or calling only deals with the balance, not the total
    elif move_type == "CALL" or move_type == "RAISE":
        state["bet_money"][player_index] += updates.amount
        state["held_money"][player_index] -= updates.amount

    send_data = {
        "bet_money": state["bet_money"],
        "held_money": state["held_money"]
    }

    helpers.update_game_state(updates.table_id, send_data)


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
