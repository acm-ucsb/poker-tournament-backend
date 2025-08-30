import asyncio
from enum import Enum
from typing import Any, Literal

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.core.card import Card
from src.core.table import TableData, TableUpdateData

class UpdateCode(Enum):
    # Table logic
    TABLE_CLOSED = 101

    # Seating logic
    PLAYER_JOINED = 201
    PLAYER_LEFT = 202
    BUTTON_MOVED = 203

    # Game logic
    PLAYER_ACTED = 301
    HAND_DEALT = 301
    CC_DEALT = 302
    SHOWDOWN = 303
    PAYOUT = 304
    BLIND_AMOUNT_UPDATED = 305
    PLAYER_ELIMINATED = 306

    # Other logic
    GAME_MESSAGE = 401


class BasePayload(BaseModel):
    pass


class PlayerJoinedPayload(BasePayload):
    player_id: str = Field(serialization_alias="player-id")
    seat: int


class PlayerLeftPayload(BasePayload):
    player_id: str = Field(serialization_alias="player-id")


class ButtonMovedPayload(BasePayload):
    button_seat: int = Field(serialization_alias="dealer-seat")
    small_blind_seat: int = Field(serialization_alias="small-blind-seat")
    big_blind_seat: int = Field(serialization_alias="big-blind-seat")


class PlayerActedPayload(BasePayload):
    player_id: str = Field(serialization_alias="player-id")
    action: Literal["FOLD", "CALL", "CHECK", "RAISE", "ALL-IN"]
    amount: int


class HandDealtPayload(BasePayload):
    player_id: str = Field(serialization_alias="player-id")
    cards: list[Card]


class CCDealtPayload(BasePayload):
    cards: list[Card]


class Payout(BaseModel):
    player_id: str = Field(serialization_alias="player-id")
    amount: int


class PayoutPayload(BasePayload):
    payouts: list[Payout]


class PlayerEliminatedPayload(BasePayload):
    player_id: str = Field(serialization_alias="player-id")


class GameMessagePayload(BasePayload):
    message: str


class UpdateData(BaseModel):
    code: UpdateCode
    payload: BasePayload


class BroadcastChannel:
    def __init__(self, max_connection: int = 12):
        self.connections: list[WebSocket] = []
        self.max_connection: int = max_connection

    async def connect(self, websocket: WebSocket, table_state: TableData) -> None:
        """
        Raises:
            ConnectionError: if max connection reached
        """
        if len(self.connections) == self.max_connection:
            raise ConnectionError

        await websocket.accept()

        # send the current game state, so that frontend can init properly
        await websocket.send_json(table_state.model_dump(mode="json", by_alias=True))

        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        asyncio.create_task(websocket.close())
        self.connections.remove(websocket)

    def disconnect_all(self) -> None:
        for connection in self.connections:
            asyncio.create_task(connection.close())

        self.connections = []

    async def _broadcast(self, msg: Any) -> None:
        """broadcast to a connection, if failed remove the connection"""
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(msg)
            except WebSocketDisconnect:
                disconnected.append(connection)

        self.connections = [
            connection
            for connection in self.connections
            if connection not in disconnected
        ]

    def update(self, state: TableData, update: TableUpdateData):
        msg = {
            "current-state": state.model_dump(mode="json", by_alias=True),
            "update-log": update.model_dump(mode="json", by_alias=True),
        }

        asyncio.create_task(self._broadcast(msg))
