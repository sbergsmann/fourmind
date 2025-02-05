"""
Old message format: [#{id}] {sender} ({time}s ago): {message}
"""

from datetime import datetime as DateTime
from typing import Dict, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: int
    sender: str
    message: str
    time: DateTime

    def __str__(self) -> str:
        return "[#{id}] {sender}: {message}".format(
            id=self.id, sender=self.sender, message=self.message  # time=(DateTime.now() - self.time).seconds,
        )


class RichChatMessage(BaseModel):
    # base data
    id: int
    message: str
    time: DateTime

    # enriched data
    sender: str
    receiver: str
    factual_information: str
    self_revelation: str
    relationship: str
    appeal: str
    linked_messages: List[int]

    def __str__(self) -> str:
        receiver: str = "- Receivers: " + self.receiver if self.receiver else "directed to: unclear"
        linked_to: str = (
            "- Linked Messages: " + "[" + ", ".join(["#" + str(id) for id in self.linked_messages]) + "]"
            if self.linked_messages
            else ""
        )
        return """[#{id}] {sender}: {message}
    {receivers}
    - Factual Info: {factual_information}
    - Self-Revelation: {self_revelation}
    - Appeal: {appeal}
    {linked_to}""".format(
            id=self.id,
            sender=self.sender,
            # time=(DateTime.now() - self.time).seconds,
            message=self.message,
            receivers=receiver,
            factual_information=self.factual_information,
            self_revelation=self.self_revelation,
            appeal=self.appeal,
            linked_to=linked_to,
        )


class Chat(BaseModel):
    id: int
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    player1: str
    player2: str
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

    def format_participants(self) -> str:
        return f"{self.player1}, {self.player2}, {self.bot}"  # TODO perhaps shuffle the order

    def _update_last_message_time(self, time: DateTime) -> None:
        self.last_message_time = time

    @property
    def humans(self):
        return [self.player1, self.player2]

    @property
    def participants(self):
        return [self.player1, self.player2, self.bot]

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
    chat: Chat = Chat(id=1, player1="Alice", player2="Bob", bot="AI", language="en")
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
            receiver="Bob",
            factual_information="Alice is good",
            self_revelation="Alice is polite",
            relationship="Friendly",
            appeal="Engage in conversation",
            linked_messages=[1, 2],
        ),
        RichChatMessage(
            id=5,
            sender="Bob",
            message="I'm doing well, thanks for asking!",
            time=chat.start_time + TimeDelta(seconds=10.2),
            receiver="Alice",
            factual_information="Bob is well",
            self_revelation="Bob is polite",
            relationship="Friendly",
            appeal="Continue conversation",
            linked_messages=[3],
        ),
    ]

    for msg in messages:
        chat.add_message(msg)

    print(chat.get_last_n_messages(3))
