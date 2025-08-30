import pathlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from gotrue import User
from src.util.auth import verify_user
from src.util.models import unauth_res, SubmittedFile
from src.util.supabase_client import db_client

import src.util.helpers as helpers

submit_router = APIRouter(prefix="/submission", tags=["submission"])

allowed_file_extensions = [".cpp", ".py"]


@submit_router.get("/", response_model=SubmittedFile, responses=unauth_res)
async def get_submitted_file(user: User = Depends(verify_user)):
    team_id = helpers.get_team_id(user)

    result = await helpers.get_file_with_stem(team_id)
    if result is None:
        # set team.has_submitted_code to false, submitted code cannot be found
        db_client.table("teams").update({"has_submitted_code": False}).eq(
            "id", team_id
        ).execute()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    filename, content = result
    return {"filename": filename, "content": content}


# if re-upload a file, old file will get deleted!
@submit_router.post("/", responses=unauth_res)
async def submit_file(file: UploadFile, user: User = Depends(verify_user)):
    helpers.check_edit_access()

    # decode bytes -> str
    # add .replace("\r\n", "\n") if want to normalize line ending wtvr
    content_str = (await file.read()).decode("utf-8")

    team_id = helpers.get_team_id(user)

    async with helpers.file_lock:
        helpers.uploads_dir.mkdir(exist_ok=True)

    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="no filename"
        )

    suffix = pathlib.Path(file.filename).suffix
    if suffix not in allowed_file_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"file extension '{suffix}' is not allowed; only {str(allowed_file_extensions)} are allowed",
        )

    team_fname = pathlib.Path(team_id + suffix)

    # joining paths
    file_path = helpers.uploads_dir / team_fname

    # delete all other team files before writing to new file. this is atomic
    await helpers.delete_file_with_stem(team_id)

    async with helpers.file_lock:
        # save the file to uploads directory
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content_str)

    # set team.has_submitted_code to true
    db_client.table("teams").update({"has_submitted_code": True}).eq(
        "id", team_id
    ).execute()

    return {"file_saved": team_fname}


@submit_router.delete("/", responses=unauth_res)
async def delete_file(user: User = Depends(verify_user)):
    helpers.check_edit_access()

    team_id = helpers.get_team_id(user)

    if not helpers.uploads_dir.is_dir():
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    team_fname = await helpers.delete_file_with_stem(team_id)

    if team_fname is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # file with team_id has been deleted! update db
    db_client.table("teams").update({"has_submitted_code": False}).eq(
        "id", team_id
    ).execute()

    return {"file_deleted": team_fname}

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
