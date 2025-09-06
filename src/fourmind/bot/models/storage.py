from typing import Dict, Set

from pydantic import BaseModel, Field

from fourmind.bot.models.chat import Chat, GameID


class ChatStorage(BaseModel):
    active_games: Set[GameID] = Field(  # pyright: ignore[reportUnknownVariableType]
        alias="activeGames", description="Set of active game IDs", default_factory=set
    )
    chats: Dict[GameID, Chat] = Field(description="Dictionary of chats", default_factory=dict)  # pyright: ignore[reportUnknownVariableType]
