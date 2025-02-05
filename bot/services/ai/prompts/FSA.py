"""This file contains the prompts for the FourSidesAnalysis model."""

SENDER: str = """The sender of the message,
which must be one of the three participants in the current chat
that sent this message.
"""

RECEIVER: str = """The user that the message is directed to, must only be one user!"""

FACTUAL_INFORMATION: str = """The factual information side of the message,
representing the data and facts conveyed.
"""

SELF_REVELATION: str = """What does the sender reveal about themselves and how it can potentially be used against them in the context of the Turing Game.
"""  # noqa E501

RELATIONSHIP: str = """The relationship side of the message,
reflecting the sender's view of their relationship with the receiver in the context of the Turing Game.
"""

APPEAL: str = """What does the sender want the receiver to do or think in the context of the Turing Game.
"""

RELATED_MESSAGES: str = """To which message is the current message a response?
Message IDs should be used to refer to messages."""
