import os
from fastapi import APIRouter
import models

game_router = APIRouter(prefix="/game", tags=["game"])


@game_router.get("/{game_id}")
def read_gamestate(game_id: int):
    return models.GameState(
        community_cards=[models.Card(rank=1, suit=1)],
        num_players=8,
        current_round=0,
        players=[],
        action_on=0,
    )


@game_router.post("/{game_id}/next")
def next_move(game_id: int, moves: int):
    # Define the name of the directory
    directory_name = os.path.join("src", "test_data")

    # Define the number of files you want to create
    number_of_files = moves

    # Create the target directory if it doesn't already exist
    # The exist_ok=True argument prevents an error if the directory is already there
    os.makedirs(directory_name, exist_ok=True)

    # Loop to create the files
    for i in range(1, number_of_files + 1):
        # Create the full file path by joining the directory and filename
        file_path = os.path.join(directory_name, f"file_{i}.txt")

        # Open the file in write mode ('w') to create it, then immediately close it.
        # The 'with' statement handles closing the file automatically.
        with open(file_path, "w") as fp:
            fp.write("making money moves")

    print(
        f"✅ Successfully created {number_of_files} files in the '{directory_name}' directory."
    )

    # should return the gamestate after the move was made.
