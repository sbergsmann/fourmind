""""""

import asyncio
from logging import Logger
from typing import Dict

from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletion, ParsedChatCompletionMessage

from bot.common import LoggerFactory
from bot.models.chat import Chat, ChatMessage, RichChatMessage
from bot.models.storage import ChatStorage
from bot.services.ai import prompts
from bot.services.ai.models import FourSidesAnalysis


class QueueProcessor:
    logger: Logger = LoggerFactory.setup_logger(__name__)
    BASE_MODEL: str = "gpt-4o-mini-2024-07-18"
    TEMPERATURE: float = 0.65

    def __init__(self, storage: ChatStorage, client: AsyncOpenAI) -> None:
        self.__storage: ChatStorage = storage
        self.client: AsyncOpenAI = client

        self.queues: Dict[int, asyncio.Queue[int]] = dict()
        self.tasks: Dict[int, asyncio.Task[None]] = dict()
        self.running_flags: Dict[int, bool] = dict()

    def add_queue(self, id: int) -> None:
        self.queues[id] = asyncio.Queue()
        self.running_flags[id] = True
        task: asyncio.Task[None] = asyncio.create_task(self.process_queue(id=id))
        self.tasks[id] = task

    async def enqueue_item_async(self, id: int, item: int) -> None:
        await self.queues[id].put(item)
        self.logger.debug(
            f"{str(self.__storage.chats[id])} Enqueued item {item} | queue size: {self.queues[id].qsize()}"
        )

    async def dequeue_and_cancel_async(self, id: int) -> None:
        self.running_flags[id] = False
        await self.queues[id].join()
        if not self.tasks[id].cancelled():
            self.tasks[id].cancel()

        try:
            _ = self.queues.pop(id)
            _ = self.tasks.pop(id)
        except KeyError:
            self.logger.warning(f"Queue or Task for id {id} not found on delete attempt.")

    async def process_queue(self, id: int) -> None:
        """An async method deployed as a separate task for each queue.

        The method processes the queue of messages for a chat with the given ID.
        """
        chat_ref: Chat = self.__storage.chats[id]
        self.logger.info(f"{str(chat_ref)} Queue up and running.")

        while self.running_flags[id]:
            # get
            message_id: int = await self.queues[id].get()
            self.logger.debug(f"Processing message with ID {message_id}")

            message: ChatMessage | RichChatMessage | None = chat_ref.get_message(message_id)
            if message is None:
                self.logger.error(f"Message with ID {message_id} not found in chat {str(chat_ref)}")
                continue
            elif isinstance(message, RichChatMessage):
                self.logger.info(f"Skipping RichChatMessage with ID {message_id}")
                continue

            # act
            rich_chat_message: RichChatMessage | None = await self._infer_async(chat_ref, message)

            # set
            if rich_chat_message is not None:
                chat_ref.add_message(rich_chat_message)

        self.logger.info(f"Queue for chat {str(chat_ref)} has been stopped.")

    async def _infer_async(self, chat_ref: Chat, message: ChatMessage) -> RichChatMessage | None:
        """Executes an async api call to openai to analyze the message.

        Analysis is based on Four Sides Method from Friedemann Schulz von Thun.
        """
        try:
            response: ParsedChatCompletion[FourSidesAnalysis] = await self.client.beta.chat.completions.parse(
                model=self.BASE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompts.FourSides.system.format(
                            ai_user=chat_ref.bot,
                            target_user=chat_ref.humans[0],
                            blamed_user=chat_ref.humans[1],
                            game_description=prompts,
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompts.FourSides.instruction.format(
                            participants=", ".join(chat_ref.participants),
                            chat_history=chat_ref.get_formatted_chat_history(stop_id=message.id),
                            message=str(message),
                        ),
                    },
                ],
                temperature=self.TEMPERATURE,
                response_format=FourSidesAnalysis,
            )
        except Exception as e:
            self.logger.error(f"Failed to infer response: {e}")
            return None

        response_message: ParsedChatCompletionMessage[FourSidesAnalysis] = response.choices[0].message
        if not response_message.parsed:
            self.logger.warning(f"Failed to parse response: {response_message.refusal}")
            return None

        self.logger.debug("Successfully parsed response")
        analysis_response: FourSidesAnalysis = response_message.parsed
        rich_chat_message: RichChatMessage = RichChatMessage.from_base(message, analysis_response, chat_ref)
        return rich_chat_message
