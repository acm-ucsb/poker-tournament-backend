from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from fastapi import WebSocketDisconnect
from pydantic import BaseModel, Field, PrivateAttr

from src.core.card import Card

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.core.table import TableState


class UpdateCode(Enum):
    # Table logic
    TABLE_CLOSED = "table_closed"

    # Seating logic
    PLAYER_JOINED = "player-joined"
    PLAYER_LEFT = "player-left"
    BUTTON_MOVED = "button-moved"

    # Game logic
    PLAYER_ACTED = "player_acted"
    HAND_DEALT = "hand-dealt"
    CC_DEALT = "cc-dealt"
    SHOWDOWN = "showdown"
    PAYOUT = "payout"
    BLIND_AMOUNT_UPDATED = "blind-amount-updated"
    PLAYER_ELIMINATED = "player-eliminated"
    NEW_HAND = "new-hand"

    # Other logic
    GAME_MESSAGE = "game-message"


class BasePayload(BaseModel):
    _code: UpdateCode = PrivateAttr()


class TableClosedPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.TABLE_CLOSED)


class PlayerJoinedPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.PLAYER_JOINED)
    player_id: str = Field(serialization_alias="player-id")
    seat: int


class PlayerLeftPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.PLAYER_LEFT)
    player_id: str = Field(serialization_alias="player-id")


class ButtonMovedPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.BUTTON_MOVED)
    button_seat: int = Field(serialization_alias="dealer-seat")
    small_blind_seat: int = Field(serialization_alias="small-blind-seat")
    big_blind_seat: int = Field(serialization_alias="big-blind-seat")


class PlayerActedPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.PLAYER_ACTED)
    player_id: str = Field(serialization_alias="player-id")
    action: Literal["FOLD", "CALL", "CHECK", "RAISE", "ALL-IN"]
    amount: int


class HandDealtPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.HAND_DEALT)
    player_id: str = Field(serialization_alias="player-id")
    cards: list[Card]


class CCDealtPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.CC_DEALT)
    cards: list[Card]


class ShowdownPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.SHOWDOWN)


class PayoutPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.PAYOUT)
    payouts: dict[str, int]


class BlindAmountUpdatePayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.BLIND_AMOUNT_UPDATED)


class PlayerEliminatedPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.PLAYER_ELIMINATED)
    player_id: str = Field(serialization_alias="player-id")


class NewHandPayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.NEW_HAND)


class GameMessagePayload(BasePayload):
    _code = PrivateAttr(default=UpdateCode.GAME_MESSAGE)
    message: str


class BroadcastChannel:
    def __init__(self, max_connection: int = 12):
        self.connections: list[WebSocket] = []
        self.max_connection: int = max_connection

    async def connect(self, websocket: WebSocket, table_state: TableState) -> None:
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

    def update(self, payload: BasePayload):
        msg = {
            "code": payload._code.value,
            "info": payload.model_dump(mode="json", by_alias=True),
        }

        asyncio.create_task(self._broadcast(msg))
