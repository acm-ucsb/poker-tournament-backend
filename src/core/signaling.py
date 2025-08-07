from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from typing import Callable

class SignalType(Enum):    
    REQUEST_STOP_GAME = 3
    REQUEST_RESUME_GAME = 4
    
    PLAYER_ELIMINATED = 5
    
    GAME_ERROR = 501
    TABLE_ASSIGNMENT_ERROR = 502
    TABLE_REASSIGNMENT_ERROR = 503
    
type Subscriber = Callable[[SignalType], None]

class EventNotifier:
    def __init__(self):
        self.subscribers: list[Subscriber] = []
        
    def subscribe(self, subscriber: Subscriber) -> None:
        self.subscribers.append(subscriber)
        
    def notify(self, signal: SignalType) -> None:
        for subscriber in self.subscribers:
            subscriber(signal)