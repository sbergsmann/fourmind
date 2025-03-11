"""This module contains the FourMind Bot, which is a subclass of TuringBotClient."""

import asyncio
import random
import signal
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from logging import Logger
from typing import Any, Dict, List, override

from openai import AsyncOpenAI
from TuringBotClient import TuringBotClient  # type: ignore

from bot.common import LoggerFactory
from bot.models.chat import Chat, ChatMessage
from bot.models.storage import ChatStorage
from bot.services.ai import ChatSimulator, QueueProcessor
from bot.services.ai.llm_inference import LLMConfig
from bot.services.ai.response_generator import IResponseGenerator
from bot.services.storage import StorageHandler


class FourMind(TuringBotClient):
    DEFAULT_LANGUAGE: str = "en"
    BOT_NAME: str = "FourMind"
    COGNITIVE_LOAD_OFFSET: float = 1.5

    logger: Logger = LoggerFactory.setup_logger(__name__)
    __event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def __init__(
        self,
        turinggame_api_key: str,
        openai_api_key: str,
        bot_name: str = BOT_NAME,
        language: str = DEFAULT_LANGUAGE,
        persist_chats: bool = True,
    ) -> None:
        super().__init__(api_key=turinggame_api_key, bot_name=bot_name, languages=language)  # type: ignore

        self.oai_client: AsyncOpenAI = AsyncOpenAI(api_key=openai_api_key)
        self.persist_chats: bool = persist_chats
        self.logger.info(f"Persist chats is set to '{persist_chats}'")

        self.__storage = ChatStorage()
        self.chats: StorageHandler = StorageHandler(storage=self.__storage, persist=persist_chats)
        self.queues: QueueProcessor = QueueProcessor(
            storage=self.__storage,
            client=self.oai_client,
            llmconfig=LLMConfig(
                base_model="gpt-4o-mini-2024-07-18",
                temperature=0.45,
            ),
        )
        self.response_generator: IResponseGenerator = ChatSimulator(
            client=self.oai_client,
            llmconfig=LLMConfig(
                base_model="gpt-4o-mini-2024-07-18",
                temperature=0.70,
            ),
        )
        self.is_message_generating: Dict[int, int] = {}
        self.followup_message: Dict[int, str] = {}
        # indicates whether a message generation is currently running

    # Override Methods (5)

    @override
    async def async_start_game(self, game_id: int, bot: str, players_list: List[str], language: str) -> bool:  # type: ignore
        """Override method to implement game start logic."""
        chat: Chat = Chat(id=game_id, humans=players_list, bot=bot, language=language)
        self.chats.add(chat)
        self.queues.add_queue(game_id)
        self.is_message_generating[game_id] = 0

        # self.__event_loop.create_task(self.start_proactive_loop_async(game_id))
        return True

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str | None:  # type: ignore
        incoming_message_start_time: DateTime = DateTime.now()
        if self.is_message_generating.get(game_id) == 1:
            self.logger.info(f"Message generation already in progress for {self.anonymize_id(game_id)}")
            return None
        self.is_message_generating[game_id] = 1

        chat_ref: Chat | None = self.chats.get(game_id)
        if chat_ref is None:
            self.logger.error(f"Chat with ID {self.anonymize_id(game_id)} not found in storage")
            return None

        chat_message: ChatMessage = ChatMessage(
            id=len(chat_ref.messages),
            sender=player,
            message=message,
            time=incoming_message_start_time,
        )

        # Chat Message enqueuing logic
        chat_ref.add_message(chat_message)
        await self.queues.enqueue_item_async(game_id, chat_message.id)
        self.logger.info(f"{str(chat_ref)} Added message to queue")

        # response handling logic
        if self.followup_message.get(game_id) is not None:
            self.logger.debug(f"Followup message found for {self.anonymize_id(game_id)}")
            response = self.followup_message[game_id]
            self.followup_message.pop(game_id)
        else:
            response: str | None = await self.response_generator.generate_response_async(chat_ref)

        if response is None:
            self.is_message_generating[game_id] = 0
            return None

        response_message: str = self.cut_message(response, game_id)
        await self.simulate_message_writing(incoming_message_start_time, response_message)
        self.is_message_generating[game_id] = 0
        return response_message

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

    # New Methods (3)

    @staticmethod
    def anonymize_id(game_id: int) -> str:
        """Anonymize an ID to only show the last four digits with three dots before them."""
        game_id_str = str(game_id)
        return f"...{game_id_str[-4:]}"

    def win_shutdown_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for SIGINT and SIGTERM."""
        self.logger.info(f"Received signal {signum}. Shutting down...")
        self.__event_loop.create_task(self._on_shutdown(True))

    async def simulate_message_writing(self, start_time: DateTime, message: str) -> None:
        """Simulate the time it takes to write a message."""
        # random variable of how long a keystroke takes
        random_keystroke_time: float = random.uniform(0.1, 0.2)
        # simulate the time it takes to write the message
        await asyncio.sleep(
            max(
                0,
                random_keystroke_time * len(message)
                - (DateTime.now() - start_time).total_seconds()
                + self.COGNITIVE_LOAD_OFFSET,
            )
        )

    def cut_message(self, message: str, game_id: int) -> str:
        """Cut the response at the first comma."""
        split_message = message.split(", ")
        if len(split_message) == 1 or random.random() < 0.5:
            return message
        elif len(split_message) > 1 and random.random() < 0.5:
            self.followup_message[game_id] = split_message[1]
            return split_message[0]
        return message.split(", ")[0].split(". ")[0]

    async def start_proactive_loop_async(self, game_id: int) -> None:
        """"""
        chat: Chat | None = self.chats.get(game_id)

        while chat:
            # start chat proactively
            if (
                chat.last_message_id == 0
                and random.random() < 0.5
                and self.is_message_generating[game_id] == 0
            ):
                self.is_message_generating[game_id] = 1
                start_message: str = "hi"
                await self.simulate_message_writing(chat.start_time, start_message)
                await self.send_game_message(game_id, start_message)  # type: ignore
                self.is_message_generating[game_id] = 0

            # if too much time has passed since the last message, send a proactive message
            elif (
                DateTime.now() - chat.last_message_time > TimeDelta(seconds=60)
                and random.random() < 0.7
                and self.is_message_generating[game_id] == 0
            ):
                self.is_message_generating[game_id] = 1
                self.logger.info(f"Proactive loop for {self.anonymize_id(game_id)}")
                response: str | None = await self.response_generator.generate_response_async(
                    chat, proactive=True
                )
                if response is not None:
                    self.logger.debug(f"Proactive message: {response}")
                    await self.send_game_message(game_id, response)
                self.is_message_generating[game_id] = 0
                await asyncio.sleep(10)

            await asyncio.sleep(4)
            chat: Chat | None = self.chats.get(game_id)

        self.logger.info(f"Proactive loop ended for {self.anonymize_id(game_id)}")
