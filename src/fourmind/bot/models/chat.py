import random
from datetime import datetime as DateTime
from datetime import timedelta
from typing import Any, Dict, List

from pydantic import BaseModel, Field

__all__ = ["Chat", "ChatMessage", "RichChatMessage", "GameID", "Message"]


type GameID = int
type Message = ChatMessage | RichChatMessage


class ChatMessage(BaseModel):
    """Basic chat message format for incoming messages."""

    # base data
    id: int
    sender: str
    message: str
    time: DateTime

    # helpers
    __str_template__: str = "[#{id}] ({time} ago) {sender}: {message}"

    def __str__(self) -> str:
        return self.__str_template__.format(
            id=self.id, sender=self.sender, message=self.message, time=self.format_time()
        )

    def format_time(self) -> str:
        """Format the time difference of the message to now.

        Returns:
            str: the formatted string.
        """
        seconds: int = (DateTime.now() - self.time).seconds

        if seconds < 60:
            return f"{seconds} sec"
        elif seconds // 60 < 0 and seconds // 3600 < 1:
            return f"{seconds // 60} min"
        else:
            return f"{seconds // 3600} hr"


class RichChatMessage(ChatMessage):
    """Rich chat message format for enriched messages after analysis."""

    # enriched data
    receivers: List[str]
    factual_information: str
    self_revelation: str
    relationship: str
    appeal: str

    # helpers
    __str_template__: str = """\
[#{id}] ({time} ago) {sender}: {message}
- Receivers: {receivers}
- Factual Info: {factual_information}
- Self-Revelation: {self_revelation}
- Relationship: {relationship}
- Appeal: {appeal}"""

    def __str__(self) -> str:
        return self.__str_template__.format(
            id=self.id,
            time=self.format_time(),
            sender=self.sender,
            message=self.message,
            receivers=self.receivers if self.receivers else "Unknown",
            factual_information=self.factual_information,
            self_revelation=self.self_revelation,
            relationship=self.relationship,
            appeal=self.appeal,
        )

    @staticmethod
    def from_base(base: ChatMessage, analysis: Any, chat_ref: "Chat") -> "RichChatMessage":
        referred_messages: List[ChatMessage | RichChatMessage | None] = [
            chat_ref.get_message(id) for id in analysis.referring_message_ids
        ]
        receivers: List[str] = list(set([msg.sender for msg in referred_messages if msg is not None]))
        return RichChatMessage(
            id=base.id,
            message=base.message,
            time=base.time,
            sender=analysis.sender,
            receivers=receivers,
            factual_information=analysis.factual_information,
            self_revelation=analysis.self_revelation,
            relationship=analysis.relationship,
            appeal=analysis.appeal,
        )


class Chat(BaseModel):
    id: GameID
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    humans: List[str]
    bot: str
    language: str
    messages: Dict[int, Message] = Field(default_factory=dict)

    __str_template__: str = """\
# Chat History
Chat Start Time: {start_time}

Format:
[#Id] (Time since Start) Sender: Message
- (optional Four-Sides Analysis)
----------------------------------------
{messages}
"""

    def add_message(self, message: Message) -> None:
        self.messages[message.id] = message
        self.last_message_time = message.time

    def get_message(self, id: int) -> Message | None:
        return self.messages.get(id)

    def get_last_n_messages(self, n: int) -> List[Message]:
        min_id: int = max(0, self.last_message_id - n)
        return [message for id, message in self.messages.items().__reversed__() if id > min_id]

    def get_formatted_chat_history(self, stop_id: int | None = None) -> str:
        """Get the formatted chat history.

        :param stop_id: on which message shall be stopped, defaults to None
        :return: a formatted string representation of the chat history.
        """
        if stop_id is None:
            stop_id = self.last_message_id

        messages: str = "\n".join([str(message) for id, message in self.messages.items() if id <= stop_id])
        start_time: str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        return self.__str_template__.format(
            start_time=start_time,
            messages=messages,
        )

    @property
    def participants(self) -> List[str]:
        """Get a shuffled list of participants.

        :return: A list of participants in random order.
        """
        shuffled_participants: List[str] = [*self.humans, self.bot]
        random.shuffle(shuffled_participants)
        return shuffled_participants

    @property
    def duration(self) -> timedelta:
        """Get the duration of the chat.

        :return: a timedelta object representing the duration of the chat.
        """
        return DateTime.now() - self.start_time

    @property
    def last_message_id(self) -> int:
        """Get the ID of the last message.

        :return: The ID of the last message in the chat.
        """
        return max(self.messages.keys(), default=0)

    def __str__(self) -> str:
        """Get a string representation of the chat.

        :return: A string representation of the chat with a hidden ID.
        """
        return "(ID {id}, #{nr_messages}, {duration}s)".format(
            id="..." + str(self.id)[-4:], nr_messages=len(self.messages), duration=self.duration.seconds
        )
