from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import game

app = FastAPI()
app.include_router(game.game_router)


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


@app.websocket("/ws/")
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


# demo code routes
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
