"""

TODO:
- Add docstrings
- Different response prompt if last message was from bot
"""

from logging import Logger
from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletionMessage, ParsedChatCompletion

from bot.common import LoggerFactory
from bot.models.chat import Chat
from bot.services.ai import prompts
from bot.services.ai.models import BotResponse


class ResponseGenerator:
    logger: Logger = LoggerFactory.setup_logger(__name__)
    BASE_MODEL: str = "gpt-4o-mini-2024-07-18"
    TEMPERATURE: float = 0.65

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client: AsyncOpenAI = client

    async def generate_response_async(self, chat_ref: Chat) -> BotResponse | None:
        try:
            response: ParsedChatCompletion[BotResponse] = await self.client.beta.chat.completions.parse(
                model=self.BASE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompts.RG.SYSTEM.format(
                            user=chat_ref.bot,
                            game_description=prompts.GAME.GAME_DESCRIPTION
                        )
                    },
                    {
                        "role": "user",
                        "content": prompts.RG.INSTRUCTION.format(
                            user=chat_ref.bot,
                            chat_history=chat_ref.get_formatted_chat_history(
                                id=chat_ref.last_message_id
                            )
                        )
                    }
                ],
                temperature=self.TEMPERATURE,
                response_format=BotResponse
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response_message: ParsedChatCompletionMessage[BotResponse] = response.choices[0].message
        if not response_message.parsed:
            self.logger.warning(f"Failed to parse response: {response_message.refusal}")
            return None

        self.logger.debug("Succesfully parsed response")
        bot_response: BotResponse = response_message.parsed
        return bot_response
