from loguru import logger


def setup_logger():
    """Setup the logger"""

    # todo: add a debug check to set the log level to debug/trace
    #   once https://github.com/MadhousePlatform/chatsharepy/pull/6 is merged
    log_level="INFO"

    logger.remove()

    try:
        logger.add("./../logs/log-{time:YYYY-MM-DD}.log",
                   backtrace=True,
                   colorize=True,
                   enqueue=True,
                   format="{time:hh:mm:ssA} <m>{level}</m> ## <c>{file}</c>::<c>{function}</c>::<c>{line}</c> ## {message}",
                   level=log_level,
                   rotation="00:00",
                   retention="14 days",
                   compression="tar.gz"
                   )
    except Exception as e:
        print(f"Error setting up logger: {e}")
