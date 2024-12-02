""""""

from typing import List
from pydantic import BaseModel, Field

from bot.services.ai import prompts


class FourSidesAnalysis(BaseModel):
    sender: str = Field(description=prompts.FSA.SENDER)
    receivers: List[str] = Field(description=prompts.FSA.RECEIVERS)
    factual_information: str = Field(description=prompts.FSA.FACTUAL_INFORMATION)
    self_revelation: str = Field(description=prompts.FSA.SELF_REVELATION)
    relationship: str = Field(description=prompts.FSA.RELATIONSHIP)
    appeal: str = Field(description=prompts.FSA.APPEAL)
    linked_messages: List[int] = Field(description=prompts.FSA.LINKED_MESSAGES)


class BotResponse(BaseModel):
    message: str | None = Field(
        description="The message to send based on the given chat history."
    )
