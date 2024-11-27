"""The StorageHandler class is responsible for managing the storage of chats in the bot.

It has methods to add, get, and remove chats from the storage, as well as persisting chats
to a persistent storage.
This class shall be the only interface to interact with the storage of chats in the bot.
"""

from logging import Logger
from models.chat import Chat
from models.storage import Storage
from common import LoggerFactory


class StorageHandler:
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self, storage: Storage | None = None):
        self.storage: Storage = storage if storage is not None else Storage()

    def get_chat(self, chat_id: int) -> Chat | None:
        if chat_id in self.storage.active_games:
            return self.storage.chats[chat_id]
        return None

    def add_chat(self, chat: Chat) -> None:
        if chat.id in self.storage.active_games:
            self.logger.error(f"Chat with ID {chat.id} already exists in storage")
            raise ValueError(f"Chat with ID {chat.id} already exists in storage")
        self.storage.active_games.add(chat.id)
        self.storage.chats[chat.id] = chat

    def remove_chat(self, chat_id: int, persist: bool) -> None:
        if chat_id in self.storage.active_games:
            self.storage.active_games.remove(chat_id)
            try:
                chat = self.storage.chats.pop(chat_id)
                if persist:
                    self._persist(chat)
            except KeyError:
                self.logger.error(f"Chat with ID {chat_id} not found in storage")

    def _persist(self, chat: Chat) -> None:
        raise NotImplementedError("persist must be implemented by the subclass")
