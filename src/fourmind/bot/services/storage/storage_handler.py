"""The StorageHandler class is responsible for managing the storage of chats in the bot.

It has methods to add, get, and remove chats from the storage, as well as persisting chats
to a persistent storage.
This class shall be the only interface to interact with the storage of chats in the bot.
"""

import os
from logging import Logger

from fourmind.bot.common.logger_factory import LoggerFactory
from fourmind.bot.models.chat import Chat
from fourmind.bot.models.storage import ChatStorage


class StorageHandler:
    logger: Logger = LoggerFactory.setup_logger(__name__)
    STORE_PATH: str = os.path.abspath("data")
    logger.info(f"Store path: {STORE_PATH}")

    def __init__(self, storage: ChatStorage, persist: bool) -> None:
        self.__storage: ChatStorage = storage
        self.persist: bool = persist

        if not os.path.exists(self.STORE_PATH):
            os.makedirs(self.STORE_PATH)
            self.logger.info(f"Store path created: {self.STORE_PATH}")

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
                self.logger.debug(f"{str(chat)} removed from storage.")
            except KeyError:
                self.logger.error(f"Chat with ID {id} not found in storage")

    def _persist(self, chat: Chat) -> None:
        """Store the chat in a .json file."""
        with open(os.path.join(self.STORE_PATH, f"chat_{str(chat.id)[-8:]}.json"), "w") as file:
            file.write(chat.model_dump_json(indent=4))
            self.logger.debug(f"{str(chat)} persisted to file.")
