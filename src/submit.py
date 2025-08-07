import os
import subprocess
import pathlib

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from gotrue import User
from src.util.auth import verify_user
from src.util.models import auth_required_responses
from src.util.supabase_client import db_client
import asyncio

submit_router = APIRouter(prefix="/submit", tags=["submit"])

# all files are sitting in this dir, <team_id>.<cpp | py>
uploads_dir = pathlib.Path("..", "poker_tournament_uploads").resolve()

# actually using a mutex, for any fs writes, preventing race conditions
file_lock = asyncio.Lock()


# if re-upload a file, old file will get deleted!
@submit_router.post("/", responses=auth_required_responses)
async def submit_file(file: UploadFile, user: User = Depends(verify_user)):
    # decode bytes -> str
    # add .replace("\r\n", "\n") if want to normalize line ending wtvr
    content_str = (await file.read()).decode("utf-8")

    # get team id from foreign key in users table
    team_id = (
        db_client.table("users").select("team_id").eq("id", user.id).single().execute()
    ).data.get("team_id")

    if team_id is None:  # means that user.team_id = NULL
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user is not associated with any team",
        )

    async with file_lock:
        uploads_dir.mkdir(exist_ok=True)

    if file.filename is not None:
        # use team id, but for now just test with the uid
        suffix = pathlib.Path(file.filename or "test.cpp").suffix
        team_fname = pathlib.Path(str(team_id) + suffix)

        # joining paths
        file_path = uploads_dir / team_fname

        async with file_lock:
            # save the file to uploads directory
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content_str)

        # set team.has_submitted_code to true
        db_client.table("teams").update({"has_submitted_code": True}).eq(
            "id", team_id
        ).execute()

        return {"file_saved_as": team_fname}

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # if file.filename.endswith(".py"):
    #     process = subprocess.run(
    #         ["python3", file.filename],
    #         capture_output=True,
    #         text=True,
    #         check=True,  # ensure the command raises exception on failure
    #         cwd=uploads_dir,  # change directory to uploads
    #     )
    #     return {
    #         "status": "success",
    #         "stdout": process.stdout,
    #         "stderr": process.stderr,
    #         "message": "Python file processed successfully.",
    #     }
    # elif file.filename.endswith(".cpp"):
    #     fname_no_ext = file.filename[:-4]
    #     exec_cmd = f"{fname_no_ext}.exe" if os.name == "nt" else f"./{fname_no_ext}"

    #     process = subprocess.run(
    #         f"c++ {file.filename} -o {fname_no_ext} && {exec_cmd}",
    #         shell=True,  # run the command in the shell, not list of args
    #         capture_output=True,
    #         text=True,
    #         check=True,  # ensure the command raises exception on failure
    #         cwd=uploads_dir,  # change directory to uploads
    #     )

    #     return {
    #         "status": "success",
    #         "stdout": process.stdout,
    #         "stderr": process.stderr,
    #         "message": "C++ file processed successfully.",
    #     }
    # else:
    #     return {
    #         "status": "error",
    #         "message": "Unsupported file type. Only .py and .cpp files are allowed.",
    #     }
