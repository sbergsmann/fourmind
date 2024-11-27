"""This module contains the FourMind Bot, which is a subclass of TuringBotClient."""

import asyncio
from logging import Logger
import signal
from TuringBotClient import TuringBotClient  # type: ignore
from typing import Any, Dict, override
from openai import AsyncOpenAI
from datetime import datetime as DateTime

from services.storage import StorageHandler
from models.chat import Chat, ChatMessage
from common import LoggerFactory


class FourMind(TuringBotClient):
    DEFAULT_LANGUAGE: str = "en"
    BOT_NAME: str = "FourMind"

    logger: Logger = LoggerFactory.setup_logger(__name__)
    __event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def __init__(
        self,
        turinggame_api_key: str,
        oai_client: AsyncOpenAI,
        bot_name: str = BOT_NAME,
        language: str = DEFAULT_LANGUAGE,
        persist_chats: bool = False
    ) -> None:
        super().__init__(  # type: ignore
            api_key=turinggame_api_key,
            bot_name=bot_name,
            languages=language
        )

        self.oai_client: AsyncOpenAI = oai_client
        self.persist_chats: bool = persist_chats

        self.storage_handler: StorageHandler = StorageHandler()
        self.is_message_generating: Dict[int, int] = {}
        # indicates whether a message generation is currently running

    # Override Methods (5)

    @override
    async def async_start_game(self, game_id: int, bot: str, pl1: str, pl2: str, language: str) -> bool:
        """Override method to implement game start logic"""
        # create a chat model
        chat: Chat = Chat(
            id=game_id,
            player1=pl1,
            player2=pl2,
            bot=bot,
            language=language
        )
        self.storage_handler.add_chat(chat)
        self.is_message_generating[game_id] = 0
        return True

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str | None:
        """Override method to implement message processing.

        Notes:
        - return type of overridden method was changed to str | None
        """
        incoming_message_start_time: DateTime = DateTime.now()
        chat: Chat | None = self.storage_handler.get_chat(game_id)
        if chat is None:
            self.logger.error(f"Chat with ID {self.anonymize_id(game_id)} not found in storage")
            return None

        chat_message: ChatMessage = ChatMessage(
            user=player,
            message=message,
            message_timedelta=chat.get_message_timedelta(incoming_message_start_time)
        )
        chat.add_message(chat_message)
        self.logger.info(
            f"{str(chat)} Added message: {chat_message.user}: {chat_message.message}"
        )

        chat.update_last_message_time(incoming_message_start_time)
        self.logger.debug(
            f"Updated chat {str(chat)}"
        )

        if player in chat.humans:
            return "Message received"  # Mocked for now
        return None

    @override
    async def async_end_game(self, game_id: int) -> None:
        """Override method to implement game end logic"""
        self.storage_handler.remove_chat(game_id, self.persist_chats)
        self.is_message_generating.pop(game_id, None)

    @override
    def start(self) -> None:
        """Override wrapper around the start method.

        Notes:
        - extended Exception handling to print and error message
        - remove the signal handlers in connect method
        """
        try:
            self.__event_loop.run_until_complete(self.connect())
        except Exception as e:
            self.logger.exception(f"Error occurred while connecting to the TuringGame API: {e}")

    @override
    def on_shutdown(self):
        """Functionless wrapper around the on_shutdown method."""
        pass

    # Non-Override Methods (2)

    async def _on_shutdown(self, send_shutdown: bool) -> None:
        """Override method to implement shutdown logic"""
        await super()._on_shutdown(send_shutdown)
        await self.oai_client.close()

    async def connect(self) -> None:
        """Extension wrapper around the connect method.

        Windows does not support AbstractEventLoop.add_signal_handler.
        """
        signal.signal(signal.SIGINT, self.win_shutdown_handler)
        signal.signal(signal.SIGTERM, self.win_shutdown_handler)
        return await super().connect()

    # New Methods (2)

    @staticmethod
    def anonymize_id(game_id: int) -> str:
        """Anonymize an ID to only show the last four digits with three dots before them."""
        game_id_str = str(game_id)
        return f"...{game_id_str[-4:]}"

    def win_shutdown_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for SIGINT and SIGTERM."""
        self.logger.info(f"Received signal {signum}. Shutting down...")
        self.__event_loop.create_task(self._on_shutdown(True))
