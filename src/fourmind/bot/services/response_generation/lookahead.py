"""Response generation module for performing simulation lookahead."""

from dataclasses import dataclass
from logging import Logger

from openai import AsyncOpenAI

from fourmind.bot.common.logger_factory import LoggerFactory
from fourmind.bot.models.chat import Chat
from fourmind.bot.models.inference import ChatSimulationReponse
from fourmind.bot.services import prompts
from fourmind.bot.services.llm_inference import LLMInference

__all__ = ["Lookahead"]


@dataclass
class SimulationConfig:
    num_simulated_messages: int = 5


class Lookahead(LLMInference):
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client: AsyncOpenAI = client

    async def simulate_chat_async(self, chat_ref: Chat, proactive: bool = False) -> str | None:
        self.logger.info(f"Simulating chat for {str(chat_ref)}")
        self.logger.info(f"Chat history: {chat_ref.get_formatted_chat_history(5, simple=True)}")
        response: ChatSimulationReponse | None = await self.ainfer(
            client=self.client,
            config=chat_ref.llmconfig,
            system_prompt=prompts.ResponseGenerationPrompts.system.format(
                game_description=prompts.GeneralPrompts.game,
                behavior=prompts.GeneralPrompts.behavior,
                target_user=chat_ref.humans[0],
                blamed_user=chat_ref.humans[1],
                ai_user=chat_ref.bot,
            ),
            instruction_prompt=prompts.ResponseGenerationPrompts.instruction.format(
                num_simulated_messages=SimulationConfig.num_simulated_messages,
                chat_history=chat_ref.get_formatted_chat_history(),
                proactive_behavior=(
                    prompts.ResponseGenerationPrompts.proactive.format(ai_user=chat_ref.bot)
                    if proactive
                    else ""
                ),
            ),
            response_model=ChatSimulationReponse,
        )

        if response is None:
            return None

        self.logger.debug(f"{str(chat_ref)} {response.messages[0].sender}: {response.messages[0].message}")
        if response.messages[0].sender == chat_ref.bot:
            return response.messages[0].message
        return None
