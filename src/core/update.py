from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from src.core.card import Card

class UpdateCode(Enum):
    # Table logic
    TABLE_CLOSED            = 101
    
    # Seating logic
    PLAYER_JOINED           = 201
    PLAYER_LEFT             = 202
    BUTTON_MOVED            = 203
    
    # Game logic
    PLAYER_ACTED            = 301
    HAND_DEALT              = 301
    CC_DEALT                = 302
    SHOWDOWN                = 303
    PAYOUT                  = 304
    BLIND_AMOUNT_UPDATED    = 305
    PLAYER_ELIMINATED       = 306
    
    # Other logic
    GAME_MESSAGE            = 401

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

