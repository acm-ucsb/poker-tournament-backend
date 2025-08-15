import asyncio
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from src.core.table import TableData, TableUpdateData

class BroadcastChannel:
    def __init__(self, max_connection: int = 12):
        self.connections: list[WebSocket] = []
        self.max_connection: int = max_connection
        
    async def connect(self, websocket: WebSocket) -> None:
        """
        Raises:
            ConnectionError: if max connection reached
        """
        if len(self.connections) == self.max_connection:
            raise ConnectionError
            
        await websocket.accept()
        
        # TODO: send the current game state, so that frontend can init properly
        # await websocket.send_json(self.table.state)
        
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        asyncio.create_task(websocket.close())
        self.connections.remove(websocket)
        
    def disconnect_all(self) -> None:
        for connection in self.connections:
            asyncio.create_task(connection.close())
            
        self.connections = []

    async def _broadcast(self, msg: Any) -> None:
        """broadcast to a connection, if failed remove the connection
        """
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(msg)
            except WebSocketDisconnect:
                disconnected.append(connection)

        self.connections = [connection for connection in self.connections if connection not in disconnected]
        
    def update(self, state: TableData, update: TableUpdateData):
        msg = {
            "current-state": state.model_dump(mode="json", by_alias=True),
            "update-log": update.model_dump(mode="json", by_alias=True),
        }
        
        asyncio.create_task(self._broadcast(msg))