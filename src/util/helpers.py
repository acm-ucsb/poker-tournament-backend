import asyncio
import os
import subprocess
import pathlib
import datetime
from fastapi import HTTPException, status
from src.util.supabase_client import db_client
from src.util.models import FileRunResult, GameState
from gotrue import User


# all files are sitting in the parent dir that the repo is in, <team_id>.<cpp | py>
uploads_dir = pathlib.Path("..", "poker_tournament_uploads").resolve()

skeleton_dir = pathlib.Path("skeleton_files").resolve()

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


def save_original_file(path: pathlib.Path, content: str):
    # save the file to uploads directory
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


# copy skeleton_file lines, insert code into correct spot, write lines to team id file
def save_insert_into_skeleton(team_id: str, suffix: str, content: str):
    lines = []
    content_lines = content.splitlines(keepends=True)
    with (skeleton_dir / f"skeleton{suffix}").open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if lines[i].startswith(r"//%insert%//"):  # the special insert string
            lines = lines[:i] + content_lines + lines[i + 1 :]
            break

    wrap_path = uploads_dir / f"wrapped_{team_id}{suffix}"
    with wrap_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


def into_stdin_format(state: GameState) -> str:
    state_str = str(state.index_to_action) + "\n"
    state_str += " ".join(state.players) + "\n"
    # only list of two cards of the current player can be shown!!! so [index_to_action]
    state_str += " ".join(state.players_cards[state.index_to_action]) + "\n"
    state_str += " ".join(map(str, state.held_money)) + "\n"
    state_str += " ".join(map(str, state.bet_money)) + "\n"
    state_str += " ".join(state.community_cards) + "\n"
    state_str += str(len(state.pots)) + "\n"
    for pot in state.pots:
        state_str += str(pot.value) + " "
        state_str += " ".join(pot.players) + "\n"
    state_str += state.current_round + "\n"
    state_str += str(state.small_blind) + "\n"
    state_str += str(state.big_blind) + "\n"

    return state_str


# no mutex for running code, files gets compiled into exe or bytecode on read
# runs the wrapped code, not the original file
async def run_file(team_id: str, state: GameState) -> FileRunResult:
    res = await get_file_with_stem(team_id)
    if res is None:
        raise ValueError
    filename = f"wrapped_{res[0]}"
    state_str = into_stdin_format(state)

    if filename.endswith(".py"):
        try:
            process = subprocess.run(
                ["python3", filename],
                capture_output=True,
                input=state_str,
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
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "message": f"Python run failed with exit code {e.returncode}: {e.cmd}",
            }
    elif filename.endswith(".cpp"):
        fname_no_ext = filename[:-4]
        exec_cmd = f"{fname_no_ext}.exe" if os.name == "nt" else f"./{fname_no_ext}"

        try:
            process = subprocess.run(
                f"c++ {filename} -o {fname_no_ext} && {exec_cmd}",
                shell=True,  # run the command in the shell, not list of args
                capture_output=True,
                input=state_str,
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
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "message": f"C++ run failed with exit code {e.returncode}: {e.cmd}",
            }
    else:
        return {
            "status": "error",
            "message": "Unsupported file type. Only .py and .cpp files are allowed.",
        }
