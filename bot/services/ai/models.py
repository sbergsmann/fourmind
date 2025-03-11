from typing import List

from pydantic import BaseModel, Field

from bot.services.ai import prompts


class FourSidesAnalysis(BaseModel):
    sender: str = Field(description=prompts.FourSides.sender)
    factual_information: str = Field(description=prompts.FourSides.factual)
    self_revelation: str = Field(description=prompts.FourSides.self_relevation)
    referring_message_ids: List[int] = Field(description=prompts.FourSides.referring_message_ids)
    # receivers: List[str] = Field(description=prompts.FourSides.receivers)
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
