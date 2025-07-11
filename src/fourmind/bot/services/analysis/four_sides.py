"""Submodule that implements the Four Sides Analysis message queue."""

import asyncio
from logging import Logger
from typing import Dict

from openai import AsyncOpenAI

from fourmind.bot.common.logger_factory import LoggerFactory
from fourmind.bot.models.chat import Chat, GameID, Message, RichChatMessage
from fourmind.bot.models.inference import FourSidesAnalysis
from fourmind.bot.models.storage import ChatStorage
from fourmind.bot.services import prompts
from fourmind.bot.services.llm_inference import LLMInference

__all__ = [
    "FourSidesQueue",
]


class FourSidesQueue(LLMInference):
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self, storage: ChatStorage, client: AsyncOpenAI) -> None:
        self.__storage: ChatStorage = storage
        self.client: AsyncOpenAI = client

        self.queues: Dict[GameID, asyncio.Queue[int]] = dict()
        self.tasks: Dict[GameID, asyncio.Task[None]] = dict()
        self.running_flags: Dict[GameID, bool] = dict()

    def add_queue(self, id: GameID) -> None:
        self.queues[id] = asyncio.Queue()
        self.running_flags[id] = True
        task: asyncio.Task[None] = asyncio.create_task(self.process_queue(id=id))
        self.tasks[id] = task

    async def enqueue_item_async(self, id: GameID, item: int) -> None:
        await self.queues[id].put(item)
        self.logger.debug(
            f"{str(self.__storage.chats[id])} Enqueued item {item} | queue size: {self.queues[id].qsize()}"
        )

    async def dequeue_and_cancel_async(self, id: GameID) -> None:
        self.running_flags[id] = False
        await self.queues[id].join()
        if not self.tasks[id].cancelled():
            self.tasks[id].cancel()

        try:
            _ = self.queues.pop(id)
            _ = self.tasks.pop(id)
        except KeyError:
            self.logger.warning(f"Queue or Task for id {id} not found on delete attempt.")

    async def process_queue(self, id: GameID) -> None:
        """An async method deployed as a separate task for each queue.

        The method processes the queue of messages for a chat with the given ID.
        """
        chat_ref: Chat = self.__storage.chats[id]
        self.logger.info(f"{str(chat_ref)} Queue up and running.")

        while self.running_flags[id]:
            # get
            message_id: int = await self.queues[id].get()
            self.logger.debug(f"Processing message with ID {message_id}")

            message: Message | None = chat_ref.get_message(message_id)
            if message is None:
                self.logger.error(f"Message with ID {message_id} not found in chat {str(chat_ref)}")
                continue
            elif isinstance(message, RichChatMessage):
                self.logger.info(f"Skipping RichChatMessage with ID {message_id}")
                continue

            analysis: FourSidesAnalysis | None = await self.ainfer(
                client=self.client,
                config=chat_ref.llmconfig,
                system_prompt=prompts.FourSidesAnalysisPrompts.system.format(
                    ai_user=chat_ref.bot,
                    game_description=prompts,
                ),
                instruction_prompt=prompts.FourSidesAnalysisPrompts.instruction.format(
                    participants=", ".join(chat_ref.participants),
                    chat_history=chat_ref.get_formatted_chat_history(last_n=message.id),
                    message=str(message),
                ),
                response_model=FourSidesAnalysis,
            )
            if analysis is None:
                self.logger.error(f"Failed to analyze message with ID {message_id}")
                continue

            rich_chat_message: RichChatMessage = RichChatMessage.from_base(message, analysis)
            chat_ref.add_message(rich_chat_message)

        self.logger.info(f"Queue for chat {str(chat_ref)} has been stopped.")
