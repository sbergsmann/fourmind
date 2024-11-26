""""""


from TuringBotClient import TuringBotClient  # type: ignore
from typing import Dict, override
from openai import AsyncOpenAI
from datetime import datetime as DateTime

from services.storage import StorageHandler
from models.chat import Chat, ChatMessage
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
        language: str = DEFAULT_LANGUAGE,
        persist_chats: bool = False
    ) -> None:
        super().__init__(  # type: ignore
            api_key=turinggame_api_key,
            bot_name=bot_name,
            languages=language
        )

        self.oai_client: AsyncOpenAI = oai_client
        self.persist_chats: bool = persist_chats

        self.storage_handler: StorageHandler = StorageHandler()
        self.is_message_generating: Dict[int, int] = {}
        # indicates whether a message generation is currently running

    @override
    async def async_start_game(self, game_id: int, bot: str, pl1: str, pl2: str, language: str) -> bool:
        """Override method to implement game start logic"""
        # create a chat model
        chat: Chat = Chat(
            id=game_id,
            player1=pl1,
            player2=pl2,
            bot=bot,
            language=language
        )
        self.storage_handler.add_chat(chat)
        self.is_message_generating[game_id] = 0
        return True

    @override
    async def async_on_message(self, game_id: int, message: str, player: str, bot: str) -> str | None:
        """Override method to implement message processing.

        Notes:
        - return type of overridden method was changed to str | None
        """
        incoming_message_start_time: DateTime = DateTime.now()
        chat: Chat | None = self.storage_handler.get_chat(game_id)
        if chat is None:
            self.logger.error(f"Chat with ID {game_id} not found in storage")
            return None

        chat_message: ChatMessage = ChatMessage(
            user=player,
            message=message,
            message_timedelta=chat.get_message_timedelta(incoming_message_start_time)
        )
        chat.add_message(chat_message)
        self.logger.info(
            f"Added message to chat with ID {game_id}: {chat_message.user}: {chat_message.message}"
        )

        chat.update_last_message_time(incoming_message_start_time)
        self.logger.info(
            f"Updated chat with ID {game_id}: #Messages: {len(chat.messages)}, Duration: {chat.duration}"
        )

        return "Message received"  # Mocked for now

    @override
    async def async_end_game(self, game_id: int) -> None:
        """Override method to implement game end logic"""
        self.storage_handler.remove_chat(game_id, self.persist_chats)
        self.is_message_generating.pop(game_id, None)

    async def _on_shutdown(self, send_shutdown: bool) -> None:
        """Override method to implement shutdown logic"""
        await super()._on_shutdown(send_shutdown)
        await self.oai_client.close()
