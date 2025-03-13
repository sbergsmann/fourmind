import random
from datetime import datetime as DateTime
from logging import Logger

from bot.common.logger_factory import LoggerFactory
from bot.models.chat import Chat


class MessageTimeSimulator:
    """A helper class simulating the spent time for following human conversational traits:

    - read and comprehend prior important messages
    - write a response
    """

    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self) -> None:
        pass

    def get_message_writing_time(self, message: str) -> float:
        """Estimate the time it takes to write a message.

        Values are taken from the following sources:
        - https://dl.acm.org/doi/10.1145/3173574.3174220
        """
        average_keystroke_time: float = max(0.06, random.gauss(0.238656, 0.1116))
        return average_keystroke_time * len(message)

    def get_cognitive_response_time(self, message: str, previous_message: str) -> float:
        """Estimate the cognitive response time (CRT) to read and comprehend the prior important messages.

        Formulas and values are taken from the following sources:
        - https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.00727/full

        Formula Variables:
        - C_e: Actor utterance (previous messages)
        - C_p: Reactor utterance (current message)

        Args:
            message (str): The message to be sent.
            previous_message (str): The last message in the chat.

        Returns:
            float: The estimated cognitive response time.
        """
        c_e = len(previous_message)
        c_p = len(message)

        crt: float = 0.15 * c_e + 0.36 * c_p + 0.0004 * c_e * c_p + 9.2

        return crt

    def calculate_remaining_response_time(self, start_time: DateTime, message: str, chat_ref: Chat) -> float:
        """Simulate the total response time for reading and writing a message."""
        actor_message: str = chat_ref.get_last_n_messages(1)[0].message
        elapsed_time: float = (DateTime.now() - start_time).total_seconds()
        total_response_time: float = max(
            0,
            self.get_message_writing_time(message)
            + self.get_cognitive_response_time(message, actor_message)
            - elapsed_time,
        )
        self.logger.debug(f"Remaining response time: {total_response_time} seconds")
        return total_response_time
