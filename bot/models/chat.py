""""""

from datetime import datetime as DateTime, timedelta as TimeDelta
from typing import List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: int
    user: str
    message: str
    message_timedelta: TimeDelta

    def __str__(self) -> str:
        return "[#{id}] {user} (after {time}s): {message}".format(
            id=self.id,
            user=self.user,
            time=self.message_timedelta.seconds,
            message=self.message
        )


class RichChatMessage(BaseModel):
    # base data
    id: int
    message: str
    message_timedelta: TimeDelta

    # enriched data
    sender: str
    receivers: List[str]
    factual_information: str
    self_revelation: str
    relationship: str
    appeal: str
    linked_messages: List[int]

    def __str__(self) -> str:
        receivers: str = (
            "- directed to: " + ", ".join(self.receivers)
            if self.receivers else "directed to: unclear"
        )
        linked_to: str = (
            "- linked to: " + "[" + ", ".join(["#" + str(id) for id in self.linked_messages]) + "]"
            if self.linked_messages else ""
        )
        return (
            """#{id} {sender} (after {time}s): {message}
    {receivers}
    - factual info: {factual_information}
    - self-revelation: {self_revelation}
    - appeal: {appeal}
    {linked_to}""".format(
                id=self.id,
                sender=self.sender,
                time=self.message_timedelta.seconds,
                message=self.message,
                receivers=receivers,
                factual_information=self.factual_information,
                self_revelation=self.self_revelation,
                appeal=self.appeal,
                linked_to=linked_to
            )
        )


class Chat(BaseModel):
    id: int
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    player1: str
    player2: str
    bot: str
    language: str
    messages: List[ChatMessage | RichChatMessage] = Field(default_factory=list)  # TODO: make it a dict

    def add_message(self, message: ChatMessage | RichChatMessage) -> None:
        self.messages.append(message)

    def get_message_timedelta(self, time: DateTime) -> TimeDelta:
        return time - self.last_message_time

    def update_last_message_time(self, time: DateTime) -> None:
        self.last_message_time = time

    def get_formatted_chat_history(self) -> str:
        messages: str = "\n".join([str(message) for message in self.messages])
        start_time: str = "Start Time: " + self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        header: str = "#MessageId User (Seconds since last message): Message"
        return f"{start_time}\n{header}\n{messages}"

    def format_participants(self) -> str:
        return f"{self.player1}, {self.player2}, {self.bot}"  # TODO perhaps shuffle the order

    @property
    def humans(self):
        return [self.player1, self.player2]

    @property
    def participants(self):
        return [self.player1, self.player2, self.bot]

    @property
    def duration(self):
        return DateTime.now() - self.start_time

    def __str__(self) -> str:
        return "(ID {id}, #{nr_messages}, {duration}s)".format(
            id="..." + str(self.id)[-4:],
            nr_messages=len(self.messages),
            duration=self.duration.seconds
        )
