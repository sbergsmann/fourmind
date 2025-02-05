""""""

from logging import Logger
import random
from typing import List

from bot.common import LoggerFactory
from bot.models.chat import Chat, ChatMessage, RichChatMessage
from bot.models.objectives import LocalResponseObjectiveConfig


class Objective:
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(
        self,
        lro_config: LocalResponseObjectiveConfig,
    ) -> None:
        self.lro_config = lro_config

    def lro(self, chat: Chat) -> float:
        """Local Response Objective"""
        # get the last 5 messages
        topK__messages: List[ChatMessage | RichChatMessage] = chat.get_last_n_messages(
            self.lro_config.rolling_message_window
        )

        # count the number of messages sent by the AI user
        bot_messages_weight = sum(
            [1 / (idx + 1) for idx, message in enumerate(topK__messages) if message.sender == chat.bot]
        )
        # calculate the local response objective
        local_response_objective: float = self.lro_config.base**bot_messages_weight
        return local_response_objective

    def ldmo(self, chat: Chat) -> bool:
        """Last Directed Message Objective"""
        # get the last message
        last_message: ChatMessage | RichChatMessage | None = chat.get_message(chat.last_message_id)
        if last_message is None:
            # chat hasnt started yet
            return True if random.random() < 0.5 else False

        if last_message.sender == chat.bot:
            # last message was sent by the AI user
            return False

        if isinstance(last_message, RichChatMessage):
            # last message was sent by the user
            if last_message.receiver == chat.bot:
                self.logger.debug(f"Last message was directed at the AI user: {last_message.id}")
                return True

            if last_message.linked_messages:
                message_ids: List[int] = last_message.linked_messages
                for message_id in message_ids:
                    message: ChatMessage | RichChatMessage | None = chat.get_message(message_id)
                    if message is None:
                        continue
                    if message.sender == chat.bot:
                        # last message was directed at the AI user
                        self.logger.debug(
                            f"A linked message of the last message was directed at the AI user: {message.id}"
                        )
                        return True
        return False
