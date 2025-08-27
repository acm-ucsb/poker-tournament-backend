from fastapi import Depends, APIRouter, HTTPException, status
from gotrue import User
from postgrest import APIError
from src.util.models import unauth_res, SubmittedFile
from src.util.auth import verify_user
from src.util.supabase_client import db_client
import src.util.helpers as helpers

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/submission/", response_model=SubmittedFile, responses=unauth_res)
async def get_submission_by_team_id(team_id: str, user: User = Depends(verify_user)):
    is_admin_res = (
        db_client.table("users").select("is_admin").eq("id", user.id).single().execute()
    )

    if not is_admin_res.data["is_admin"]:
        raise HTTPException(401, detail="user is not admin")

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
