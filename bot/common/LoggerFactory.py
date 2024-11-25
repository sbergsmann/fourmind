import logging
import os

from copy import copy
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue
import sys
from typing import Optional


class LoggerFactory:
    """Factory class for setting up and managing loggers.

    Includes enhanced features like colored logs and a queue listener."""

    log_level_str: str = os.getenv("LOG_LEVEL", "DEBUG").upper()
    LOG_LEVEL: int = getattr(logging, log_level_str, logging.DEBUG)

    # Queue to decouple log production from consumption
    _queue = SimpleQueue()  # type: ignore
    _queue_handler = QueueHandler(_queue)  # type: ignore

    # Coloring for log messages
    _color_mapping = {
        'DEBUG': 37,  # white
        'INFO': 36,   # cyan
        'WARNING': 33,  # yellow
        'ERROR': 31,  # red
        'CRITICAL': 41,  # white on red bg
    }
    _prefix = '\033['
    _suffix = '\033[0m'

    class ColoredFormatter(logging.Formatter):
        """Custom formatter to apply color coding to log levels."""
        def __init__(self, fmt: str | None = None, **kwargs):  # type: ignore
            super().__init__(fmt, **kwargs)  # type: ignore

        def format(self, record: logging.LogRecord) -> str:
            rec = copy(record)
            levelname = rec.levelname
            seq = LoggerFactory._color_mapping.get(levelname, 37)  # Default to white
            colored_levelname = f"{LoggerFactory._prefix}{seq}m{levelname}{LoggerFactory._suffix}"
            rec.levelname = colored_levelname
            return super().format(rec)

    # Use sys.stdout to mimic print behavior
    _stream_handler = logging.StreamHandler(stream=sys.stdout)
    _stream_handler.setFormatter(
        ColoredFormatter(
            fmt='[%(asctime)s] %(levelname)s - %(filename)s:%(lineno)d(%(funcName)s): %(message)s'
        )
    )

    # Initialize the queue listener
    _queue_listener = QueueListener(_queue, _stream_handler)  # type: ignore
    _queue_listener.start()

    @staticmethod
    def setup_logger(
        name: str,
        level: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ) -> logging.Logger:
        """
        Sets up a logger with the specified name, log level, queue handler, and queue listener.

        Args:
            name (str): Name of the logger.
            level (Optional[int]): Logging level. Defaults to LoggerFactory.LOG_LEVEL.
            logger (Optional[logging.Logger]): Existing logger instance to configure.

        Returns:
            logging.Logger: Configured logger instance.
        """
        if level is None:
            level = LoggerFactory.LOG_LEVEL

        if logger is None:
            logger = logging.getLogger(name)
        else:
            # Remove all handlers to avoid duplicate logs
            for handler in logger.handlers:
                logger.removeHandler(handler)

        # Set log level only once
        logger.setLevel(level)

        # Avoid adding duplicate handlers
        if not logger.handlers:
            logger.addHandler(LoggerFactory._queue_handler)

        return logger
