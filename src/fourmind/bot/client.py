"""This module implements the FourMind Bot, which is a subclass of TuringBotClient."""

import asyncio
import platform
import random
import signal
import time
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from logging import Logger
from typing import Any, Dict, List, override

import websockets
from openai import AsyncOpenAI
from turing_bot_client import TuringBotClient  # type: ignore
from turing_bot_client.TuringBotClient import APIKeyMessage  # type: ignore

from fourmind.bot.common.logger_factory import LoggerFactory
from fourmind.bot.models.chat import Chat, ChatMessage, GameID
from fourmind.bot.models.storage import ChatStorage
from fourmind.bot.services.analysis.four_sides import FourSidesQueue
from fourmind.bot.services.response_generation.lookahead import Lookahead
from fourmind.bot.services.response_generation.message_time_simulator import MessageTimeSimulator
from fourmind.bot.services.storage.storage_handler import StorageHandler


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
        persist_chats: bool = False,
    ) -> None:
        super().__init__(api_key=turinggame_api_key, bot_name=bot_name, languages=language)  # type: ignore

        self.oai_client: AsyncOpenAI = AsyncOpenAI(api_key=openai_api_key)
        self.persist_chats: bool = persist_chats
        self.logger.info(f"Persist chats is set to '{persist_chats}'")
        self.lock = asyncio.Lock()

        self.__storage = ChatStorage()
        self.chats: StorageHandler = StorageHandler(storage=self.__storage, persist=persist_chats)
        self.queues: FourSidesQueue = FourSidesQueue(storage=self.__storage, client=self.oai_client)
        self.response_generator: Lookahead = Lookahead(client=self.oai_client)
        self.mts = MessageTimeSimulator()

        # indicates whether a message generation is currently running
        self.response_generation_lock: Dict[GameID, int] = {}

        # temp buffer for cutted messages
        self.followup_message: Dict[GameID, str] = {}

    # Override Methods (5)

    @override
    async def async_start_game(
        self,
        game_id: GameID,
        bot: str,
        players_list: List[str],
        language: str,
    ) -> bool:
        """Override method to implement game start logic."""
        chat: Chat = Chat(id=game_id, players=players_list, bot=bot, language=language)
        await self.chats.add(chat)
        self.queues.add_queue(game_id)
        self.response_generation_lock[game_id] = 0

        self.__event_loop.create_task(self.start_proactive_loop_async(game_id))
        return True

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str | None:  # type: ignore
        incoming_message_start_time: DateTime = DateTime.now()

        chat_ref: Chat | None = await self.chats.get(game_id)
        if chat_ref is None:
            self.logger.error(f"Chat with ID {self.anonymize_id(game_id)} not found in storage")
            return None

        if player != bot:
            await self.new_message(
                chat_ref=chat_ref,
                game_id=game_id,
                message=message,
                sender=player,
                time=incoming_message_start_time,
            )

        if self.response_generation_lock.get(game_id) == 1:
            self.logger.info(f"{str(chat_ref)} Message generation already in progress")
            return None
        self.response_generation_lock[game_id] = 1

        # response handling logic
        if self.followup_message.get(game_id) is not None:
            self.logger.debug(f"Followup message found for {self.anonymize_id(game_id)}")
            response = self.followup_message.pop(game_id)
        else:
            response: str | None = await self.response_generator.simulate_chat_async(chat_ref)

        if response is None:
            self.response_generation_lock[game_id] = 0
            return None

        response_message: str | None = self.post_process_message(response, game_id, bot)
        if response_message is None:
            self.response_generation_lock[game_id] = 0
            return None

        remaining_response_time: float = self.mts.calculate_remaining_response_time(
            incoming_message_start_time, response_message, chat_ref
        )
        await asyncio.sleep(remaining_response_time)
        await self.new_message(
            chat_ref=chat_ref,
            game_id=game_id,
            message=response_message,
            sender=bot,
            time=DateTime.now(),
        )
        self.response_generation_lock[game_id] = 0
        return response_message

    @override
    async def async_end_game(self, game_id: int) -> None:
        """Override method to implement game end logic"""
        await self.chats.remove(game_id)
        await self.queues.dequeue_and_cancel_async(game_id)
        self.response_generation_lock.pop(game_id, None)

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

    @override
    async def connect(self) -> None:
        """Connect to the TuringGame API and start the main loop.
        This method will handle the connection to the API and the main loop for processing messages.
        """
        if platform.system() == "Windows":
            signal.signal(signal.SIGINT, self.win_shutdown_handler)
            signal.signal(signal.SIGTERM, self.win_shutdown_handler)
        else:
            # Use event loop signal handlers on Unix-like systems
            self.__event_loop.add_signal_handler(signal.SIGINT, self._on_shutdown_wrapper)
            self.__event_loop.add_signal_handler(signal.SIGTERM, self._on_shutdown_wrapper)

        self.logger.info("Starting to connect now")

        while not self._shutdown_flag:
            try:
                async with websockets.connect(self.api_endpoint) as _websocket:
                    self.logger.info("connected, checking api key...")
                    if hasattr(self, "accuse_ready"):
                        self.logger.debug(f"accuse_ready: {self.accuse_ready}")
                        await _websocket.send(
                            APIKeyMessage(
                                api_key=self.api_key,
                                bot_name=self.bot_name,
                                languages=self.languages,
                                accuse_ready=self.accuse_ready,
                            ).model_dump_json()
                        )
                    else:
                        await _websocket.send(
                            APIKeyMessage(
                                api_key=self.api_key, bot_name=self.bot_name, languages=self.languages
                            ).model_dump_json()
                        )
                    self._websocket = _websocket
                    response = await self._receive()
                    if response["type"] == "info":
                        self.logger.debug(f"Server Response: {response['message']}")
                    await self._main_loop()

            except websockets.exceptions.ConnectionClosedOK as e:
                self.logger.debug(f"Connection closed with code: {e.code}, reason: {e.reason}")
                break

            except websockets.exceptions.ConnectionClosedError as e:
                self.logger.debug(f"Connection closed with code: {e.code}")
                if e.code == 1008:
                    if e.reason == "invalid api key request":
                        self.logger.error("Your API key was rejected. Please check your API Key")
                    elif e.reason == "invalid language codes":
                        self.logger.error(
                            "Your language codes are not in the correct format or not accepted as allowed languages"  # noqa: E501
                        )
                    await self._on_shutdown(send_shutdown=False)
                else:
                    self.logger.debug("Game currently not reachable, waiting to reconnect...")
                    # time.sleep(5)
                    continue

            except ConnectionRefusedError:
                self.logger.debug("Connection refused, retry...")
                time.sleep(5)
                continue
            except websockets.exceptions.InvalidStatus:
                self.logger.debug("Connection refused, retry...")
                time.sleep(5)
                continue
            except Exception as e:
                self.logger.exception(f"Unexpected error: {e}")
                time.sleep(5)
                continue

    @override
    def on_gamemaster_message(self, game_id: int, message: str, player: str, bot: str) -> None:
        pass

    # Non-Override Methods (1)

    async def _on_shutdown(self, send_shutdown: bool) -> None:
        """Override method to implement shutdown logic"""
        await super()._on_shutdown(send_shutdown)
        await self.oai_client.close()

    # New Methods (3)

    async def new_message(
        self,
        chat_ref: Chat,
        game_id: GameID,
        message: str,
        sender: str,
        time: DateTime,
    ) -> None:
        async with self.lock:
            chat_message: ChatMessage = ChatMessage(
                id=len(chat_ref.messages),
                sender=sender,
                message=message,
                time=time,
            )
            chat_ref.add_message(chat_message)
            await self.queues.enqueue_item_async(game_id, chat_message.id)

    @staticmethod
    def anonymize_id(game_id: int) -> str:
        """Anonymize an ID to only show the last four digits with three dots before them."""
        game_id_str = str(game_id)
        return f"...{game_id_str[-4:]}"

    def win_shutdown_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for SIGINT and SIGTERM."""
        self.logger.info(f"Received signal {signum}. Shutting down...")
        self.__event_loop.create_task(self._on_shutdown(True))

    FORBIDDEN_WORDS: List[str] = ["nah ", "i think ", "i mean ", "just ", "like ", "kinda ", "sort of "]

    def post_process_message(self, message: str, game_id: int, bot: str) -> str | None:
        """Cut the response at the first comma and filter forbidden words."""
        # failsave since bot tends to repeat itself
        current_chat: Chat | None = self.__storage.chats.get(game_id)
        if current_chat is not None:
            previous_messages: List[str] = [
                msg.message.lower() for msg in current_chat.get_last_n_messages(3) if msg.sender == bot
            ]
            if message.lower() in previous_messages:
                return None

        for word in self.FORBIDDEN_WORDS:
            message = message.replace(word, "")

        split_message = message.split(", ")
        if len(split_message) == 1 or random.random() < 0.5:
            return message
        elif len(split_message) > 1 and random.random() < 0.5:
            self.followup_message[game_id] = split_message[1]
            return split_message[0]
        return message.split(", ")[0].split(". ")[0]

    async def start_proactive_loop_async(self, game_id: int) -> None:
        """"""
        await asyncio.sleep(2)
        chat: Chat | None = await self.chats.get(game_id)

        while chat:
            if TimeDelta(minutes=20) < DateTime.now() - chat.start_time:
                self.logger.info(f"Ending game for {self.anonymize_id(game_id)} due to timeout")
                await self.async_end_game(game_id)
                break

            if len(chat.messages) < 6:
                proactive_condition: bool = (
                    DateTime.now() - chat.last_message_time > TimeDelta(seconds=10)
                    and self.response_generation_lock[game_id] == 0
                )
            else:
                proactive_condition: bool = (
                    DateTime.now() - chat.last_message_time > TimeDelta(seconds=30)
                    and random.random() < 0.7
                    and self.response_generation_lock[game_id] == 0
                )

            # start chat proactively
            if (
                chat.last_message_id == 0
                and random.random() < 0.5
                and self.response_generation_lock[game_id] == 0
            ):
                self.response_generation_lock[game_id] = 1
                start_message: str = random.choice(["hi", "hello", "hi there"])
                remaining_response_time: float = self.mts.calculate_remaining_response_time(
                    chat.start_time, start_message, chat
                )
                await asyncio.sleep(remaining_response_time)
                await self.new_message(
                    chat_ref=chat,
                    game_id=game_id,
                    message=start_message,
                    sender=chat.bot,
                    time=DateTime.now(),
                )
                self.response_generation_lock[game_id] = 0
                await self.send_game_message(game_id, start_message)  # type: ignore

            # if too much time has passed since the last message, send a proactive message
            elif proactive_condition:
                self.response_generation_lock[game_id] = 1
                self.logger.info(f"Proactive loop for {self.anonymize_id(game_id)}")
                response: str | None = await self.response_generator.simulate_chat_async(chat, proactive=True)
                if response is not None:
                    self.logger.debug(f"Proactive message: {response}")
                    await self.new_message(
                        chat_ref=chat,
                        game_id=game_id,
                        message=response,
                        sender=chat.bot,
                        time=DateTime.now(),
                    )
                    await self.send_game_message(game_id, response)
                self.response_generation_lock[game_id] = 0
                await asyncio.sleep(10)

            await asyncio.sleep(4)
            chat: Chat | None = await self.chats.get(game_id)

        self.logger.info(f"Proactive loop ended for {self.anonymize_id(game_id)}")


def main() -> None:
    """Main function to run the bot."""
    import os

    logger: Logger = LoggerFactory.setup_logger(__name__)
    logger.info(f"Starting FourMind bot with log level {LoggerFactory.log_level_str}")

    turinggame_api_key: str | None = os.getenv("TURINGGAME_API_KEY")
    if turinggame_api_key is None:
        logger.critical("TURINGGAME_API_KEY environment variable is not set")
        return None
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        logger.critical("OPENAI_API_KEY environment variable is not set")
        return None

    persist_chats: bool = bool(os.environ.get("PERSIST_CHATS", "False"))

    bot: FourMind = FourMind(
        turinggame_api_key=turinggame_api_key,
        openai_api_key=openai_api_key,
        persist_chats=persist_chats,
    )
    logger.info("FourMind bot created")
    bot.start()


if __name__ == "__main__":
    main()
