import random
from datetime import datetime as DateTime
from datetime import timedelta
from typing import Dict, List

from pydantic import BaseModel, Field

from fourmind.bot.models.inference import FourSidesAnalysis
from fourmind.bot.services.llm_inference import LLMConfig

__all__ = ["Chat", "ChatMessage", "RichChatMessage", "GameID", "Message", "Bot"]


type GameID = int
type Bot = str
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

    def simple_str(self) -> str:
        return self.__str__()

    def format_time(self) -> str:
        """Format the time difference of the message to now.

        Returns:
            str: the formatted string.
        """
        seconds: int = (DateTime.now() - self.time).seconds

        if seconds < 60:
            return f"{seconds} sec"
        elif seconds // 3600 < 1:
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

    __base_str_template__: str = """\
[#{id}] ({time} ago) {sender}: {message}"""

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

    def simple_str(self) -> str:
        return self.__base_str_template__.format(
            id=self.id,
            time=self.format_time(),
            sender=self.sender,
            message=self.message,
        )

    @staticmethod
    def from_base(base: ChatMessage, analysis: FourSidesAnalysis) -> "RichChatMessage":
        return RichChatMessage(
            id=base.id,
            message=base.message,
            time=base.time,
            sender=analysis.sender,
            receivers=analysis.receivers,
            factual_information=analysis.factual_information,
            self_revelation=analysis.self_revelation,
            relationship=analysis.relationship,
            appeal=analysis.appeal,
        )


class Chat(BaseModel):
    id: GameID
    start_time: DateTime = Field(default_factory=DateTime.now)
    last_message_time: DateTime = Field(default_factory=DateTime.now)
    players: List[str]
    bot: str
    language: str
    messages: Dict[int, Message] = Field(default_factory=dict)  # type: ignore
    llmconfig: LLMConfig = Field(default_factory=LLMConfig)

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
        return [message for id, message in self.messages.items().__reversed__() if id >= min_id]

    def get_formatted_chat_history(self, last_n: int | None = None, simple: bool = False) -> str:
        """Get the formatted chat history.

        :param last_n: The number of last messages to include in the history.
        :return: a formatted string representation of the chat history.
        """
        if last_n is None:
            last_n = self.last_message_id

        last_n_messages: List[Message] = self.get_last_n_messages(last_n)

        if simple:
            messages: str = "\n".join([message.simple_str() for message in last_n_messages[::-1]])
        else:
            messages: str = "\n".join([str(message) for message in last_n_messages[::-1]])
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
        shuffled_participants: List[str] = list(
            set([*self.players, self.bot])
        )  # bug that bot is in humans list
        random.shuffle(shuffled_participants)
        return shuffled_participants

    @property
    def humans(self) -> List[str]:
        """Get the list of human participants.

        This property is due to a bug in the original code where the bot was included in the humans list.

        :return: A list of human participants.
        """
        humans: List[str] = list(set(self.players) - {self.bot})
        return humans

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
        return "(ID {id}, Bot={bot}, #{num_messages})".format(
            id="..." + str(self.id)[-4:], bot=self.bot, num_messages=len(self.messages)
        )
