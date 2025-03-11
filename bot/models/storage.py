from typing import Dict, Set

from pydantic import BaseModel, Field

from bot.models.chat import Chat


class ChatStorage(BaseModel):
    active_games: Set[int] = Field(
        alias="activeGames", description="Set of active game IDs", default_factory=set
    )
    chats: Dict[int, Chat] = Field(description="Dictionary of chats", default_factory=dict)
