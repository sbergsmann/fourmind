from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger
from typing import Any, Type

from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletion, ParsedChatCompletionMessage
from pydantic import BaseModel


@dataclass
class LLMConfig:
    base_model: str
    temperature: float


class ILLMInference(ABC):
    @abstractmethod
    async def ainfer(self, *args: Any, **kwargs: Any) -> Any: ...


class LLMInference(ILLMInference):
    FALLBACK_CONFIG: LLMConfig = LLMConfig(base_model="gpt-4o-mini-2024-07-18", temperature=0.65)

    def __init__(self, client: AsyncOpenAI, logger: Logger, config: LLMConfig | None) -> None:
        self._client: AsyncOpenAI = client
        self.logger: Logger = logger
        self.llmconfig: LLMConfig = config or self.FALLBACK_CONFIG

    async def ainfer(self, psystem: str, pinstruction: str, response_model: Type[BaseModel]) -> Any | None:
        try:
            completion: ParsedChatCompletion[BaseModel] = await self._client.beta.chat.completions.parse(
                model=self.llmconfig.base_model,
                messages=[
                    {
                        "role": "system",
                        "content": psystem,
                    },
                    {
                        "role": "user",
                        "content": pinstruction,
                    },
                ],
                temperature=self.llmconfig.temperature,
                response_format=response_model,
            )
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return None
        response: ParsedChatCompletionMessage[BaseModel] = completion.choices[0].message
        if not response.parsed:
            self.logger.warning(f"Failed to parse response: {response.refusal}")
            return None

        result: BaseModel = response.parsed
        return result
