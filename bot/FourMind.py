"""This module contains the FourMind Bot, which is a subclass of TuringBotClient."""

import asyncio
from logging import Logger
import signal
from TuringBotClient import TuringBotClient  # type: ignore
from typing import Any, Dict, override
from openai import AsyncOpenAI
from datetime import datetime as DateTime

from bot.models.storage import ChatStorage
from bot.services.ai import QueueProcessor, ResponseGenerator
from bot.services.ai.models import BotResponse
from bot.services.storage import StorageHandler
from bot.models.chat import Chat, ChatMessage
from bot.common import LoggerFactory


class FourMind(TuringBotClient):
    DEFAULT_LANGUAGE: str = "en"
    BOT_NAME: str = "FourMind"

    logger: Logger = LoggerFactory.setup_logger(__name__)
    __event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def __init__(
        self,
        turinggame_api_key: str,
        openai_api_key: str,
        bot_name: str = BOT_NAME,
        language: str = DEFAULT_LANGUAGE,
        persist_chats: bool = True
    ) -> None:
        super().__init__(  # type: ignore
            api_key=turinggame_api_key,
            bot_name=bot_name,
            languages=language
        )

        self.oai_client: AsyncOpenAI = AsyncOpenAI(api_key=openai_api_key)
        self.persist_chats: bool = persist_chats
        self.logger.info(f"Persist chats is set to '{persist_chats}'")

        self.__storage = ChatStorage()
        self.chats: StorageHandler = StorageHandler(
            storage=self.__storage,
            persist=persist_chats
        )
        self.queues: QueueProcessor = QueueProcessor(
            storage=self.__storage,
            client=self.oai_client
        )
        self.response_generator: ResponseGenerator = ResponseGenerator(
            client=self.oai_client
        )
        self.is_message_generating: Dict[int, int] = {}
        # indicates whether a message generation is currently running

    # Override Methods (5)

    @override
    async def async_start_game(self, game_id: int, bot: str, pl1: str, pl2: str, language: str) -> bool:
        """Override method to implement game start logic.

        TODO perhaps async not needed here
        """
        # create a chat model
        chat: Chat = Chat(
            id=game_id,
            player1=pl1,
            player2=pl2,
            bot=bot,
            language=language
        )
        self.chats.add(chat)
        self.queues.add_queue(game_id)
        self.is_message_generating[game_id] = 0
        return True

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str | None:
        """Override method to implement message processing.

        Notes:
        - return type of overridden method was changed to str | None
        """
        incoming_message_start_time: DateTime = DateTime.now()
        chat_ref: Chat | None = self.chats.get(game_id)
        if chat_ref is None:
            self.logger.error(f"Chat with ID {self.anonymize_id(game_id)} not found in storage")
            return None

        chat_message: ChatMessage = ChatMessage(
            id=len(chat_ref.messages),
            user=player,
            message=message,
            time=incoming_message_start_time
        )
        chat_ref.add_message(chat_message)
        await self.queues.enqueue_item_async(game_id, chat_message.id)
        self.logger.info(
            f"{str(chat_ref)} Added message to queue"
        )

        response: BotResponse | None = await self.response_generator.generate_response_async(chat_ref)
        if response is None:
            return None
        return response.message

    @override
    async def async_end_game(self, game_id: int) -> None:
        """Override method to implement game end logic"""
        self.chats.remove(game_id)
        await self.queues.dequeue_and_cancel_async(game_id)
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
