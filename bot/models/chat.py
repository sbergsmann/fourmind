"""Chat and message models for the bot."""

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


if __name__ == "__main__":
    from datetime import timedelta as TimeDelta
    from typing import List

    # Example Usage
    chat: Chat = Chat(id=1, humans=["Alice", "Bob"], bot="AI", language="en")
    messages: List[ChatMessage | RichChatMessage] = [
        ChatMessage(id=1, sender="Alice", message="Hello", time=chat.start_time + TimeDelta(seconds=1)),
        ChatMessage(
            id=2, sender="Bob", message="Hi, Alice! How are you?", time=chat.start_time + TimeDelta(seconds=3)
        ),
        ChatMessage(id=3, sender="AI", message="Hey guys", time=chat.start_time + TimeDelta(seconds=3.1)),
        RichChatMessage(
            id=4,
            sender="Alice",
            message="I'm good, thanks! How about you?",
            time=chat.start_time + TimeDelta(seconds=5.8),
            receivers=["Bob"],
            factual_information="Alice is good",
            self_revelation="Alice is polite",
            relationship="Friendly",
            appeal="Engage in conversation",
        ),
        RichChatMessage(
            id=5,
            sender="Bob",
            message="I'm doing well, thanks for asking!",
            time=chat.start_time + TimeDelta(seconds=10.2),
            receivers=["Alice"],
            factual_information="Bob is well",
            self_revelation="Bob is polite",
            relationship="Friendly",
            appeal="Continue conversation",
        ),
    ]

    for msg in messages:
        chat.add_message(msg)

    print(chat.get_last_n_messages(3))
