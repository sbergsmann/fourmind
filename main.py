""""""

from logging import Logger
import os

from dotenv import load_dotenv
is_dotenv_loaded: bool = load_dotenv()

from bot import FourMind  # noqa E402
from bot.common import LoggerFactory  # noqa E402


if __name__ == "__main__":
    logger: Logger = LoggerFactory.setup_logger(__name__)
    logger.info(f"Starting FourMind bot with log level {LoggerFactory.log_level_str}")

    logger.debug(f".env file loaded: {is_dotenv_loaded}")

    turinggame_api_key: str | None = os.getenv("TURINGGAME_API_KEY")
    if turinggame_api_key is None:
        logger.critical("TURINGGAME_API_KEY environment variable is not set")
        exit(1)

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        logger.critical("OPENAI_API_KEY environment variable is not set")
        exit(1)

    bot: FourMind = FourMind(
        turinggame_api_key=turinggame_api_key,
        openai_api_key=openai_api_key
    )
    logger.info("FourMind bot created")
    bot.start()
