""""""

from logging import Logger
from typing import Dict,  Set

from pydantic import Field, BaseModel

from bot.common import LoggerFactory
from bot.models.chat import Chat


class Storage(BaseModel):
    active_games: Set[int] = Field(
        alias="activeGames",
        description="Set of active game IDs",
        default_factory=set
    )
    chats: Dict[int, Chat] = Field(
        description="Dictionary of chats",
        default_factory=dict
    )
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def get_chat(self, chat_id: int) -> Chat | None:
        if chat_id in self.active_games:
            return self.chats[chat_id]
        return None

    def add_chat(self, chat: Chat):
        if chat.id in self.active_games:
            return None
        self.active_games.add(chat.id)
        self.chats[chat.id] = chat
        return chat

    def remove_chat(self, chat_id: int) -> Chat | None:
        if chat_id in self.active_games:
            try:
                chat = self.chats.pop(chat_id)
            except KeyError:
                self.logger.error(f"Chat with ID {chat_id} not found in storage")
                return None
            return chat
        return None

    def persist(self) -> None:
        raise NotImplementedError("persist must be implemented by the subclass")
