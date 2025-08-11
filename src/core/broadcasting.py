import asyncio
import threading

from fastapi import WebSocket, WebSocketDisconnect

class BroadcastChannel:
    def __init__(self, max_connection = 12):
        self.active_connections: list[WebSocket] = []
        self.max_connection = max_connection
        self.active_connections_mutex = threading.Lock()
        
    async def connect(self, websocket: WebSocket) -> None:
        """
        Raises:
            ConnectionError: if max connection reached
        """
        if len(self.active_connections) == self.max_connection:
            raise ConnectionError
            
        await websocket.accept()
        
        # TODO: send the current game state, so that frontend can init properly
        # await websocket.send_json(self.table.state)
        
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        asyncio.create_task(websocket.close())
        self.active_connections.remove(websocket)
        
    def disconnect_all(self) -> None:
        for connection in self.active_connections:
            asyncio.create_task(connection.close())
            
        self.active_connections = []

    async def _broadcast(self, message: str) -> None:
        """broadcast to a connection, if failed remove the connection
        """
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected_connections.append(connection)

        self.active_connections = [connection for connection in self.active_connections if connection not in disconnected_connections]
        
    def update(self, data = None):
        asyncio.create_task(self._broadcast("Game state changed!"))