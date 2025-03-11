from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger
from typing import Any

from openai import AsyncOpenAI

from bot.common import LoggerFactory
from bot.models.chat import Chat
from bot.services.ai import LLMConfig, LLMInference, prompts
from bot.services.ai.models import ChatSimulationReponse


@dataclass
class ChatSimulatorConfig:
    num_simulated_messages: int = 7


class IResponseGenerator(ABC):
    @abstractmethod
    async def generate_response_async(self, chat_ref: Chat, *args: Any, **kwargs: Any) -> str | None: ...


class ChatSimulator(IResponseGenerator, LLMInference):
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self, client: AsyncOpenAI, llmconfig: LLMConfig) -> None:
        super().__init__(client, self.logger, llmconfig)
        self.client: AsyncOpenAI = client

    async def generate_response_async(self, chat_ref: Chat, proactive: bool = False) -> str | None:
        response: ChatSimulationReponse | None = await self.ainfer(
            psystem=prompts.Simulation.system.format(
                game_description=prompts.General.game,
                behavior=prompts.General.behavior,
                target_user=chat_ref.humans[0],
                blamed_user=chat_ref.humans[1],
                ai_user=chat_ref.bot,
            ),
            pinstruction=prompts.Simulation.instruction.format(
                num_simulated_messages=ChatSimulatorConfig.num_simulated_messages,
                chat_history=chat_ref.get_formatted_chat_history(),
                proactive_behavior=(
                    prompts.Simulation.proactive.format(ai_user=chat_ref.bot) if proactive else ""
                ),
            ),
            response_model=ChatSimulationReponse,
        )

        if response is None:
            return None

        if response.messages[0].sender == chat_ref.bot:
            self.logger.debug(f"Bot: {response.messages[0].message}")
            return response.messages[0].message
        else:
            self.logger.debug(f"{response.messages[0].sender}: {response.messages[0].message}")
            return None
