""""""

import asyncio
from openai import AsyncOpenAI

from bot.models.chat import ChatMessage


class MessageAnalyzer:
    def __init__(self, client: AsyncOpenAI, queue: asyncio.Queue[ChatMessage]) -> None:
        self.client: AsyncOpenAI = client
        self.queue: asyncio.Queue[ChatMessage] = queue
