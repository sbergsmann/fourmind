"""

TODO:
- Add docstrings
- Different response prompt if last message was from bot
"""

from logging import Logger
import random  # noqa F401  # type: ignore
from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletionMessage, ParsedChatCompletion

from bot.common import LoggerFactory
from bot.models.chat import Chat
from bot.services.ai import Objective, prompts
from bot.services.ai.models import BotResponse, ChatSimulationReponse, ResponseDecision


class ResponseGenerator:
    logger: Logger = LoggerFactory.setup_logger(__name__)
    BASE_MODEL: str = "gpt-4o-mini-2024-07-18"
    TEMPERATURE: float = 0.65

    def __init__(self, client: AsyncOpenAI, objective: Objective) -> None:
        self.client: AsyncOpenAI = client
        self.objective: Objective = objective

    def _should_respond(self, chat_ref: Chat) -> bool:
        """Determine whether the bot should respond to the given chat history."""
        # lro: float = self.objective.lro(chat_ref)
        # rnd: float = random.random()
        # self.logger.debug(f"Local response objective: {lro} - rnd: {rnd}")
        # return rnd <= lro
        return self.objective.ldmo(chat_ref)

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
            response: ParsedChatCompletion[ChatSimulationReponse] = (
                await self.client.beta.chat.completions.parse(
                    model=self.BASE_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": prompts.RG.SIMULATION_SYSTEM.format(
                                game_description=prompts.game.GAME_DESCRIPTION,
                                characteristics=prompts.behavior.GENERAL_CHARACTERISTICS,
                                target_user=chat.humans[0],
                                blamed_user=chat.humans[1],
                                ai_user=chat.bot,
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompts.RG.SIMULATION_INSTRUCTION.format(
                                num_simulated_messages=7,
                                chat_history=chat.get_formatted_chat_history(),
                                proactive_behavior=(
                                    prompts.RG.PROACTIVE_BEHAVIOR.format(ai_user=chat.bot)
                                    if proactive
                                    else ""
                                ),  # noqa E501,
                            ),
                        },
                    ],
                    temperature=self.TEMPERATURE,
                    response_format=ChatSimulationReponse,
                )
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response_message: ParsedChatCompletionMessage[ChatSimulationReponse] = response.choices[0].message
        if not response_message.parsed:
            self.logger.warning(f"Failed to parse response: {response_message.refusal}")
            return None

        chat_simulation_response: ChatSimulationReponse = response_message.parsed
        # self.logger.debug(
        #     f"Instruction Prompt: {prompts.RG.SIMULATION_INSTRUCTION.format(
        #         num_simulated_messages=7,
        #         chat_history=chat.get_formatted_chat_history(),
        #     )}",
        # )
        return chat_simulation_response

    async def generate_basic_response(self, chat: Chat) -> BotResponse | None:
        try:
            response: ParsedChatCompletion[BotResponse] = await self.client.beta.chat.completions.parse(
                model=self.BASE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompts.RG.BASIC_SYSTEM.format(
                            user=chat.bot,
                            game_description=prompts.game.GAME_DESCRIPTION,
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompts.RG.BASIC_INSTRUCTION.format(
                            user=chat.bot,
                            chat_history=chat.get_formatted_chat_history(),
                        ),
                    },
                ],
                temperature=self.TEMPERATURE,
                response_format=BotResponse,
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response_message: ParsedChatCompletionMessage[BotResponse] = response.choices[0].message
        if not response_message.parsed:
            self.logger.warning(f"Failed to parse response: {response_message.refusal}")
            return None

        self.logger.debug("Successfully parsed response")
        bot_response: BotResponse = response_message.parsed
        self.logger.debug(f"Response: {bot_response}")
        return bot_response

    # Deprecated

    async def should_respond(self, chat_ref: Chat) -> bool:
        """"""
        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.BASE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": prompts.RG.OBSERVATION_SYSTEM.format(
                            user=chat_ref.bot, game_description=prompts.game.GAME_DESCRIPTION
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompts.RG.OBSERVATION_INSTRUCTION.format(
                            user=chat_ref.bot,
                            chat_history=chat_ref.get_formatted_chat_history(),
                            participants=chat_ref.format_participants(),
                        ),
                    },
                ],
                temperature=self.TEMPERATURE,
                response_format=ResponseDecision,
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return False
        message: ParsedChatCompletionMessage[ResponseDecision] = response.choices[0].message
        if message.parsed:
            response_decision: ResponseDecision = message.parsed
            self.logger.debug(f"Response decision: {response_decision}")
            return response_decision.final_decision
        self.logger.warning(f"Failed to parse response decision: {message.refusal}")
        return False
