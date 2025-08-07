import os

# import subprocess
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from gotrue import User
from src.util.auth import verify_user
from src.util.models import auth_required_responses
from src.util.supabase_client import db_client

submit_router = APIRouter(prefix="/submit", tags=["submit"])


@submit_router.post("/file/", response_model=dict, responses=auth_required_responses)
async def submit_file(file: UploadFile, user: User = Depends(verify_user)):
    try:
        content = await file.read()

        # decode bytes -> str, normalize line endings from windows to unix (eh doesn't matter)
        content_str = content.decode("utf-8")  # .replace("\r\n", "\n")

        # use team id, but for now just test with the uid
        _, extension = os.path.splitext(file.filename or "test.cpp")
        new_fname = user.id + extension

        # save the file to uploads directory
        uploads_dir = os.path.abspath(os.path.join("..", "poker_tournament_uploads"))
        os.makedirs(uploads_dir, exist_ok=True)

        if file.filename is not None:
            file_path = os.path.join(uploads_dir, new_fname)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_str)

            # get team id from foreign key in users table
            team_id_res = (
                db_client.table("users")
                .select("team_id")
                .eq("id", user.id)
                .single()
                .execute()
            )

            # set has_submitted_code to true
            db_client.table("teams").update({"has_submitted_code": True}).eq(
                "id", team_id_res.data.get("team_id")
            ).execute()

            return {"file_saved_as": new_fname}
        else:
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
