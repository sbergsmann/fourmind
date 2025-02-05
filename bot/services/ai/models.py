""""""

from typing import List
from pydantic import BaseModel, Field

from bot.services.ai import prompts


class FourSidesAnalysis(BaseModel):
    sender: str = Field(description=prompts.FSA.SENDER)
    receiver: str = Field(description=prompts.FSA.RECEIVER)
    factual_information: str = Field(description=prompts.FSA.FACTUAL_INFORMATION)
    self_revelation: str = Field(description=prompts.FSA.SELF_REVELATION)
    relationship: str = Field(description=prompts.FSA.RELATIONSHIP)
    appeal: str = Field(description=prompts.FSA.APPEAL)
    related_message_ids: List[int] = Field(description=prompts.FSA.RELATED_MESSAGES)


class BotResponse(BaseModel):
    message: str | None = Field(description="The generated response message.")


class ChatSimulationMessage(BaseModel):
    sender: str = Field(description="The sender of the message.")
    message: str = Field(description="The message content.")


class ChatSimulationReponse(BaseModel):
    messages: List[ChatSimulationMessage] = Field(
        description="""The generated response messages.
        Each message is a dictionary containing the sender and the message."""
    )


class ResponseDecision(BaseModel):
    decision: bool = Field(
        description="The decision of whether a response is needed based on the given chat history."
    )
    argumentation: str = Field(description="The argumentation for the decision.")
    final_decision: bool = Field(
        description="The made decision based on the argumentation of whether a response is needed based on the given chat history."  # noqa E501
    )
