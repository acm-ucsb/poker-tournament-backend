import os
from fastapi import Depends
from gotrue import User
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.util.models import unauth_res
from src.util.auth import verify_user

game_router = APIRouter(prefix="/game", tags=["game"])


@game_router.post(
    "/move/", responses=unauth_res, description="for human users to play???"
)
def make_move(user: User = Depends(verify_user)):
    pass


# @game_router.post("/{game_id}/next/", response_model=str)
def next_move(game_id: int, moves: int):
    # Define the name of the directory
    directory_name = os.path.join("test_data")

    # Define the number of files you want to create
    number_of_files = moves

    # i dont actually want to be able to create a billion files on my instance
    """
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
    """

    return f"✅ Successfully created {number_of_files} files in the '{directory_name}' directory."

    # should return the gamestate after the move was made.


@game_router.websocket("/{table_id}/ws")
# not sure if this is right
async def websocket_connect(*, websocket: WebSocket, table_id: str):
    # TODO: query the table_id using game_id
    # MOCK_TABLE = Table("1")
    # MOCK_CHANNEL = BroadcastChannel(MOCK_TABLE)

    # await MOCK_CHANNEL.connect(websocket)
    # MOCK_CHANNEL.update()
    # asyncio.sleep(2)
    # MOCK_CHANNEL.disconnect_all()
    pass


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(
        self,
        message: str,
        websocket: WebSocket,
        not_to_self=False,
    ):
        for connection in self.active_connections:
            if not_to_self and connection == websocket:
                pass
            else:
                await connection.send_text(message)


manager = ConnectionManager()


@game_router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            await manager.send_personal_message(f"you: {data}", websocket)
            await manager.broadcast(f"???: {data}", websocket, not_to_self=True)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("someone left the chat.", websocket)


@game_router.websocket("/table/{table_id}/ws")
async def gamestate_updator(*, websocket: WebSocket, table_id: str):
    pass
