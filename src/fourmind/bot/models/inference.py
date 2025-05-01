"""Response models for LLM inference."""

from typing import List

from pydantic import BaseModel, Field

from fourmind.bot.services import prompts

__all__ = [
    "FourSidesAnalysis",
    "ChatSimulationMessage",
    "ChatSimulationReponse",
]


class FourSidesAnalysis(BaseModel):
    sender: str = Field(description=prompts.FourSidesAnalysis.sender)
    factual_information: str = Field(description=prompts.FourSidesAnalysis.factual)
    self_revelation: str = Field(description=prompts.FourSidesAnalysis.self_relevation)
    referring_message_ids: List[int] = Field(description=prompts.FourSidesAnalysis.referring_message_ids)
    relationship: str = Field(description=prompts.FourSidesAnalysis.relationship)
    appeal: str = Field(description=prompts.FourSidesAnalysis.appeal)


class ChatSimulationMessage(BaseModel):
    sender: str = Field(description="The sender of the message.")
    message: str = Field(description="The message content.")


class ChatSimulationReponse(BaseModel):
    messages: List[ChatSimulationMessage] = Field(
        description="""The generated response messages.
        Each message is a dictionary containing the sender and the message."""
    )
