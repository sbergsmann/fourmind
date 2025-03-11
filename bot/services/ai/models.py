from typing import List

from pydantic import BaseModel, Field

from bot.services.ai import prompts


class FourSidesAnalysis(BaseModel):
    sender: str = Field(description=prompts.FourSides.sender)
    receiver: str = Field(description=prompts.FourSides.receiver)
    factual_information: str = Field(description=prompts.FourSides.factual)
    self_revelation: str = Field(description=prompts.FourSides.self_relevation)
    relationship: str = Field(description=prompts.FourSides.relationship)
    appeal: str = Field(description=prompts.FourSides.appeal)


class ChatSimulationMessage(BaseModel):
    sender: str = Field(description="The sender of the message.")
    message: str = Field(description="The message content.")


class ChatSimulationReponse(BaseModel):
    messages: List[ChatSimulationMessage] = Field(
        description="""The generated response messages.
        Each message is a dictionary containing the sender and the message."""
    )
