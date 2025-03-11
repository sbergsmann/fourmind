import random
from datetime import datetime as DateTime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


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
    id: int
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    humans: List[str]
    bot: str
    language: str
    messages: Dict[int, ChatMessage | RichChatMessage] = Field(default_factory=dict)

    def add_message(self, message: ChatMessage | RichChatMessage) -> None:
        self.messages[message.id] = message
        self._update_last_message_time(message.time)

    def get_message(self, id: int) -> ChatMessage | RichChatMessage | None:
        return self.messages.get(id)

    def get_last_n_messages(self, n: int) -> List[ChatMessage | RichChatMessage]:
        min_id: int = max(0, self.last_message_id - n)
        return [message for id, message in self.messages.items().__reversed__() if id > min_id]

    def get_formatted_chat_history(self, pov: str | None = None, stop_id: int | None = None) -> str:
        if stop_id is None:
            stop_id = self.last_message_id

        if pov is None:
            messages: str = "\n".join(
                [str(message) for id, message in self.messages.items() if id <= stop_id]
            )
        else:
            # pov = chat.bot
            messages: str = "\n".join(
                [
                    str(message).replace(pov, f"{pov} (You)")
                    for id, message in self.messages.items()
                    if id <= stop_id
                ]
            )

        start_time: str = "Start Time: " + self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        header: str = "[#Id] Sender: Message"
        return f"{start_time}\n{header}\n{messages}"

    def _update_last_message_time(self, time: DateTime) -> None:
        self.last_message_time = time

    @property
    def participants(self) -> List[str]:
        shuffled_participants: List[str] = [*self.humans, self.bot]
        random.shuffle(shuffled_participants)
        return shuffled_participants

    @property
    def duration(self):
        return DateTime.now() - self.start_time

    @property
    def last_message_id(self) -> int:
        return max(self.messages.keys(), default=0)

    def __str__(self) -> str:
        return "(ID {id}, #{nr_messages}, {duration}s)".format(
            id="..." + str(self.id)[-4:], nr_messages=len(self.messages), duration=self.duration.seconds
        )
