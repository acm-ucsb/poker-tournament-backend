import os
import subprocess
from fastapi import APIRouter
from src.util.auth import verify_user
from src.util.models import auth_required_responses

submit_router = APIRouter(prefix="/submit", tags=["submit"])


@submit_router.post("/file/")
async def submit_file(file: UploadFile):
    try:
        content = await file.read()

        # decode bytes -> str, normalize line endings from windows to unix (eh doesn't matter)
        content_str = content.decode("utf-8")  # .replace("\r\n", "\n")

        # save the file to uploads directory
        uploads_dir = os.path.abspath(os.path.join("..", "poker_backend_uploads"))
        os.makedirs(uploads_dir, exist_ok=True)

        if file.filename is not None:
            file_path = os.path.join(uploads_dir, file.filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_str)
        else:
            raise ValueError("Filename is missing in the uploaded file.")

        if file.filename.endswith(".py"):
            process = subprocess.run(
                ["python3", file.filename],
                capture_output=True,
                text=True,
                check=True,  # ensure the command raises exception on failure
                cwd=uploads_dir,  # change directory to uploads
            )
            return {
                "status": "success",
                "stdout": process.stdout,
                "stderr": process.stderr,
                "message": "Python file processed successfully.",
            }
        elif file.filename.endswith(".cpp"):
            fname_no_ext = file.filename[:-4]
            exec_cmd = f"{fname_no_ext}.exe" if os.name == "nt" else f"./{fname_no_ext}"

            process = subprocess.run(
                f"c++ {file.filename} -o {fname_no_ext} && {exec_cmd}",
                shell=True,  # run the command in the shell, not list of args
                capture_output=True,
                text=True,
                check=True,  # ensure the command raises exception on failure
                cwd=uploads_dir,  # change directory to uploads
            )

            return {
                "status": "success",
                "stdout": process.stdout,
                "stderr": process.stderr,
                "message": "C++ file processed successfully.",
            }
        else:
            return {
                "status": "error",
                "message": "Unsupported file type. Only .py and .cpp files are allowed.",
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
