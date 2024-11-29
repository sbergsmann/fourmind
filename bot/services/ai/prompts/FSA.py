"""This file contains the prompts for the FourSidesAnalysis model."""

SENDER: str = """The sender of the message,
which must be one of the three participants in the current chat
that sent this message.
"""

RECEIVERS: str = """The receivers of the message,
which must be one of the three participants in the current chat or
any combination of them if it is not clear based on the chat history and context
to whom this message was directed.
"""

FACTUAL_INFORMATION: str = """The factual information side of the message,
representing the data and facts conveyed.
"""

SELF_REVELATION: str = """The self-revelation side of the message,
indicating what the sender reveals about themselves
"""

RELATIONSHIP: str = """The relationship side of the message,
reflecting the sender's view of their relationship with the receiver
"""

APPEAL: str = """The appeal side of the message,
expressing what the sender wants the receiver to do or think
"""

LINKED_MESSAGES: str = """Which potential messages does the current message refer to?
To which message is the current message a response?
To minimize ambiguity, never link all messages in a chat.
Message IDs should be used to refer to messages."""
