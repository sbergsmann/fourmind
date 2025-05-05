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
    sender: str = Field(description=prompts.FourSidesAnalysisPrompts.sender)
    factual_information: str = Field(description=prompts.FourSidesAnalysisPrompts.factual)
    self_revelation: str = Field(description=prompts.FourSidesAnalysisPrompts.self_relevation)
    relationship: str = Field(description=prompts.FourSidesAnalysisPrompts.relationship)
    appeal: str = Field(description=prompts.FourSidesAnalysisPrompts.appeal)
    receivers: List[str] = Field(description=prompts.FourSidesAnalysisPrompts.receivers)


class ChatSimulationMessage(BaseModel):
    sender: str = Field(description="The sender of the message.")
    message: str = Field(description="The message content.")


class ChatSimulationReponse(BaseModel):
    messages: List[ChatSimulationMessage] = Field(
        description="""The generated response messages.
        Each message is a dictionary containing the sender and the message."""
    )
