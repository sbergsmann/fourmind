""""""

from logging import Logger
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

from FourMind import FourMind
from common import LoggerFactory


if __name__ == "__main__":
    logger: Logger = LoggerFactory.setup_logger(__name__)
    logger.debug("Starting FourMind bot")

    is_dotenv_loaded: bool = load_dotenv()
    logger.debug(f".env file loaded: {is_dotenv_loaded}")

    turinggame_api_key: str | None = os.getenv("TURINGGAME_API_KEY")
    if turinggame_api_key is None:
        logger.critical("TURINGGAME_API_KEY environment variable is not set")
        exit(1)

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        logger.critical("OPENAI_API_KEY environment variable is not set")
        exit(1)

    oai_client: AsyncOpenAI = AsyncOpenAI(api_key=openai_api_key)

    bot: FourMind = FourMind(
        turinggame_api_key=turinggame_api_key,
        oai_client=oai_client
    )
    logger.info("FourMind bot created")
    bot.start()
