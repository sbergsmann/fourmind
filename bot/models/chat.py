""""""

from datetime import datetime as DateTime, timedelta as TimeDelta
from typing import List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    user: str
    message: str
    message_timedelta: TimeDelta


class Chat(BaseModel):
    id: int
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    player1: str
    player2: str
    bot: str
    language: str
    messages: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def get_message_timedelta(self, time: DateTime) -> TimeDelta:
        return time - self.last_message_time

    def update_last_message_time(self, time: DateTime) -> None:
        self.last_message_time = time

    @property
    def humans(self):
        return [self.player1, self.player2]

    @property
    def duration(self):
        return DateTime.now() - self.start_time

    def __str__(self) -> str:
        return "(ID {id}, #{nr_messages}, {duration}s)".format(
            id="..." + str(self.id)[-4:],
            nr_messages=len(self.messages),
            duration=self.duration.seconds
        )
