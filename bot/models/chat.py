""""""

from datetime import datetime as DateTime, timedelta as TimeDelta
from typing import List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    user: str
    message: str
    message_timedelta: TimeDelta


class Chat(BaseModel):
    id: int
    start_time: DateTime
    last_message_time: DateTime
    player1: str
    player2: str
    bot: str
    messages: List[ChatMessage]

    @property
    def humans(self):
        return [self.player1, self.player2]

    @property
    def duration(self):
        return DateTime.now() - self.start_time
