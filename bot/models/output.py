""""""

from typing import List
from pydantic import BaseModel, Field


class FourSidesAnalysis(BaseModel):
    sender: str = Field(
        description="""The sender of the message,
        which must be one of the three paricipants in the current chat
        that sent this message.
        """
    )
    receivers: List[str] = Field(
        description="""The receivers(s) of the message,
        which must be one of the three paricipants in the current chat or
        any combination of them if it is not clear based on the chat history and context
        to whom this message was directed.
        """
    )
    factual_information: str = Field(
        description="""The factual information side of the message,
        representing the data and facts conveyed.
        """
    )
    self_revelation: str = Field(
        description="""The self-revelation side of the message,
        indicating what the sender reveals about themselves
        """
    )
    relationship: str = Field(
        description="""The relationship side of the message,
        reflecting the sender's view of their relationship with the receiver
        """
    )
    appeal: str = Field(
        description="""The appeal side of the message,
        expressing what the sender wants the receiver to do or think
        """
    )
    linked_messages: List[int] = Field(
        description="""Which potential messages does the current message refer to?
        To which message is the current message a response?
        To minimize ambiguity, never link all messages in a chat.
        Message IDs should be used to refer to messages.
        """
    )
