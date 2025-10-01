"""Pydantic models for experiment data."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

__all__ = ["Bot", "SeverinMetadata", "Message", "PlayerInfoItem", "GameData"]


class Bot(BaseModel):
    name: str
    color: str
    colorID: str


class SeverinMetadata(BaseModel):
    userID: str
    gameID: int
    city: str
    age: str
    education: str
    it_education: str
    created_at: str
    updated_at: str


class Message(BaseModel):
    gameID: int
    oldidx: Optional[int]
    color: str
    userID: str
    botID: int
    message: str
    create_time: str
    colorID: str
    messageidx: int


class PlayerInfoItem(BaseModel):
    decision_time: Optional[Any]
    username: str
    score: float


class GameData(BaseModel):
    gameID: int
    starttime: str
    duration: str
    botmodel: str
    prompt: str
    winner: str
    createTS: str
    updateTS: str
    language: str
    bots: List[Bot]
    severin_metadata: SeverinMetadata
    botname: str
    messages: List[Message]
    player_info: Dict[str, PlayerInfoItem]
