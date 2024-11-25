""""""


from TuringBotClient import TuringBotClient  # type: ignore
import asyncio
from typing import override
from openai import AsyncOpenAI


from common import LoggerFactory


class FourMind(TuringBotClient):
    DEFAULT_LANGUAGE: str = "en"
    BOT_NAME: str = "FourMind"

    logger = LoggerFactory.setup_logger(__name__)

    def __init__(
        self,
        turinggame_api_key: str,
        oai_client: AsyncOpenAI,
        bot_name: str = BOT_NAME,
        language: str = DEFAULT_LANGUAGE
    ) -> None:
        super().__init__(  # type: ignore
            api_key=turinggame_api_key,
            bot_name=bot_name,
            languages=language
        )

        self.oai_client: AsyncOpenAI = oai_client

    @override
    def start(self) -> None:
        self.__event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        try:
            self.__event_loop.run_until_complete(super().connect())
            self.logger.info("FourMind bot started")
        except Exception as e:
            self.logger.exception(f"Error occurred while connecting to the TuringGame API: {e}")

    @override
    async def async_start_game(self, game_id: int, bot: str, pl1: str, pl2: str, language: str) -> bool:
        """Override method to implement game start logic"""
        raise NotImplementedError("async_start_game must be implemented by the subclass")

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str:
        """Override method to implement message processing"""
        raise NotImplementedError("async_on_message must be implemented by the subclass")

    @override
    async def async_end_game(self, game_id: int) -> None:
        """Override method to implement game end logic"""
        raise NotImplementedError("async_end_game must be implemented by the subclass")

    async def _on_shutdown(self, send_shutdown: bool) -> None:
        """Override method to implement shutdown logic"""
        await super()._on_shutdown(send_shutdown)
        await self.oai_client.close()
