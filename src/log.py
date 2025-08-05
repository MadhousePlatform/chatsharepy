"""
Logging configuration module for the application.

This module provides functionality to set up and configure logging using the loguru library.
It implements a file-based logging system with the following features:
- Daily log rotation at midnight
- 14-day log retention policy
- Compressed archive storage (tar.gz)
- Colored log output
- Detailed formatting including timestamp, log level, file location, and message
- Backtrace support for better error debugging
"""

from loguru import logger


def setup_logger():
    """Setup the logger"""

    # pylint: disable=fixme
    # todo: add a debug check to set the log level to debug/trace
    #   once https://github.com/MadhousePlatform/chatsharepy/pull/6 is merged
    log_level = "INFO"

    logger.remove()

    logger.add("./../logs/log-{time:YYYY-MM-DD}.log",
               backtrace=True,
               colorize=True,
               format="{time:hh:mm:ssA} <m>{level}</m> "
                      "## <c>{file}</c>::<c>{function}</c>::<c>{line}</c> "
                      "## {message}",
               level=log_level,
               rotation="00:00",
               retention="14 days",
               compression="tar.gz"
               )
