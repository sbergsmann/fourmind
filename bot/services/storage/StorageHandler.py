"""The StorageHandler class is responsible for managing the storage of chats in the bot.

It has methods to add, get, and remove chats from the storage, as well as persisting chats
to a persistent storage.
This class shall be the only interface to interact with the storage of chats in the bot.
"""

from logging import Logger

from bot.models.chat import Chat
from bot.models.storage import ChatStorage
from bot.common import LoggerFactory


class StorageHandler:
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self, storage: ChatStorage, persist: bool = False) -> None:
        self.__storage: ChatStorage = storage
        self.persist: bool = persist

    def get(self, id: int) -> Chat | None:
        if id in self.__storage.active_games:
            return self.__storage.chats.get(id)
        return None

    def add(self, obj: Chat) -> None:
        if obj.id in self.__storage.active_games:
            self.logger.error(f"Chat with ID {obj.id} already exists in storage")
            raise ValueError(f"Chat with ID {obj.id} already exists in storage")
        self.__storage.active_games.add(obj.id)
        self.__storage.chats[obj.id] = obj

    def remove(self, id: int) -> None:
        if id in self.__storage.active_games:
            self.__storage.active_games.remove(id)
            try:
                chat = self.__storage.chats.pop(id)
                if self.persist:
                    self._persist(chat)
            except KeyError:
                self.logger.error(f"Chat with ID {id} not found in storage")

    async def remove_async(self, id: int) -> None:
        self.logger.warning("remove_async is not implemented for ChatHandler")

    def _persist(self, chat: Chat) -> None:
        raise NotImplementedError("persist must be implemented by the subclass")
