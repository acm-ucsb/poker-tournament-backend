import asyncio
import pathlib
import datetime
from fastapi import HTTPException, status
from src.util.supabase_client import db_client
from gotrue import User


# all files are sitting in the parent dir that the repo is in, <team_id>.<cpp | py>
uploads_dir = pathlib.Path("..", "poker_tournament_uploads").resolve()

# actually using a mutex, for any fs writes, preventing race conditions
file_lock = asyncio.Lock()


# raises exception if cannot edit
def check_edit_access():
    can_users_edit = True

    # hardcoded tournament id to check submission deadline
    res = (
        db_client.table("tournaments")
        .select("submissions_deadline")
        .eq("id", "f6fd507b-42fb-4fba-a0d3-e9ded05aeca5")
        .single()
        .execute()
    )

    submission_deadline = datetime.datetime.strptime(
        res.data["submissions_deadline"], "%Y-%m-%dT%H:%M:%S%z"
    )

    # users can edit if current time < deadline
    can_users_edit = (
        datetime.datetime.now(tz=datetime.timezone.utc) < submission_deadline
    )

    if not can_users_edit:
        raise HTTPException(
            status_code=403, detail="files cannot be updated at this time"
        )


def get_team_id(user: User):
    # get team id from foreign key in users table
    team_id = (
        db_client.table("users").select("team_id").eq("id", user.id).single().execute()
    ).data.get("team_id")

    if team_id is None:  # means that user.team_id = NULL
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user is not associated with any team",
        )

    return str(team_id)


# gets only the first one it sees. there should only be one.
# returns fname, text content
async def get_file_with_stem(stem: str) -> tuple[str, str] | None:
    if uploads_dir.is_dir():
        # reading the file shouldnt need a mutex...
        # async with file_lock:
        for entry in uploads_dir.iterdir():
            if entry.is_file() and entry.stem == stem:
                return entry.name, entry.read_text(encoding="utf-8")


# deletes only the first one it sees. there should only be one.
async def delete_file_with_stem(stem: str) -> str | None:
    if uploads_dir.is_dir():
        # lock before iterdir just in case. i dont wanna get anything messed up
        async with file_lock:
            for entry in uploads_dir.iterdir():
                if entry.is_file() and entry.stem == stem:
                    entry.unlink()
                    return entry.name
