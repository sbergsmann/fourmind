"""Submodule implementing the base inference method for calling LLMs using the OpenAI format."""

from dataclasses import dataclass
from logging import Logger
from typing import Type, TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletion, ParsedChatCompletionMessage
from pydantic import BaseModel

from fourmind.bot.common.logger_factory import LoggerFactory

__all__ = [
    "LLMInference",
    "LLMConfig",
]

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


@dataclass
class LLMConfig:
    base_model: str
    temperature: float


class LLMInference:
    """This class implements the base inference method for calling LLMs using the OpenAI format."""

    FALLBACK_CONFIG: LLMConfig = LLMConfig(base_model="gpt-4o-mini-2024-07-18", temperature=0.65)
    logger: Logger = LoggerFactory.setup_logger(__name__)

    def __init__(self) -> None: ...

    async def ainfer(
        self,
        client: AsyncOpenAI,
        config: LLMConfig,
        system_prompt: str,
        instruction_prompt: str,
        response_model: Type[TBaseModel],
    ) -> TBaseModel | None:
        try:
            completion: ParsedChatCompletion[TBaseModel] = await client.beta.chat.completions.parse(
                model=config.base_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": instruction_prompt,
                    },
                ],
                temperature=config.temperature,
                response_format=response_model,
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response: ParsedChatCompletionMessage[TBaseModel] = completion.choices[0].message
        if not response.parsed:
            self.logger.warning(f"Failed to parse response: {response.refusal}")
            return None

        result: TBaseModel = response.parsed
        return result
