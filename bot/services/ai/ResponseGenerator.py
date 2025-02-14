"""

TODO:
- Add docstrings
- Different response prompt if last message was from bot
"""

from logging import Logger

from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletion, ParsedChatCompletionMessage

from bot.common import LoggerFactory
from bot.models.chat import Chat
from bot.services.ai import prompts
from bot.services.ai.models import ChatSimulationReponse


class ResponseGenerator:
    logger: Logger = LoggerFactory.setup_logger(__name__)
    BASE_MODEL: str = "gpt-4o-mini-2024-07-18"
    TEMPERATURE: float = 0.65

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client: AsyncOpenAI = client

    async def generate_response_async(self, chat_ref: Chat, proactive: bool = False) -> str | None:
        """Generate a response based on the given chat history.

        Raises:
            Exception: If the response generation fails.
        """
        # if not self._should_respond(chat_ref):
        #     return None

        response: ChatSimulationReponse | None = await self.generate_response_based_on_simulation(
            chat_ref, proactive=proactive
        )
        if response is None:
            return None
        # self.logger.debug(
        #     f"Response: {'\n'.join([f'{msg.sender}: {msg.message}' for msg in response.messages])}"
        # )

        if response.messages[0].sender == chat_ref.bot:
            self.logger.debug(f"Bot: {response.messages[0].message}")
            return response.messages[0].message
        else:
            self.logger.debug("User message")
            return None

    async def generate_response_based_on_simulation(
        self, chat: Chat, proactive: bool = False
    ) -> ChatSimulationReponse | None:
        """Generate a response based on the given chat history."""
        try:
            response: ParsedChatCompletion[
                ChatSimulationReponse
            ] = await self.client.beta.chat.completions.parse(
                model=self.BASE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompts.Simulation.system.format(
                            game_description=prompts.General.game,
                            characteristics=prompts.General.behavior,
                            target_user=chat.humans[0],
                            blamed_user=chat.humans[1],
                            ai_user=chat.bot,
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompts.Simulation.instruction.format(
                            num_simulated_messages=7,
                            chat_history=chat.get_formatted_chat_history(),
                            proactive_behavior=(
                                prompts.Simulation.proactive.format(ai_user=chat.bot) if proactive else ""
                            ),
                        ),
                    },
                ],
                temperature=self.TEMPERATURE,
                response_format=ChatSimulationReponse,
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response_message: ParsedChatCompletionMessage[ChatSimulationReponse] = response.choices[0].message
        if not response_message.parsed:
            self.logger.warning(f"Failed to parse response: {response_message.refusal}")
            return None

        chat_simulation_response: ChatSimulationReponse = response_message.parsed
        return chat_simulation_response
