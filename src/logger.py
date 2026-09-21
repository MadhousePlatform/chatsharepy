"""
logger.py
Configures the shared application logger. Log records are formatted with
monolog-python's Monolog-compatible JSON formatter and sent to syslog, so
they can be read by Laravel on the panel.
"""

import logging

from monolog import MonologHandler

from src.debug import is_debug

logger = logging.getLogger("chatshare")
logger.addHandler(MonologHandler())


def configure_logger() -> None:
    """
    Set the logger's level from the current debug state.

    Call this after parse_args() has run, so is_debug() reflects the
    --debug flag: DEBUG level when debug mode is enabled, INFO otherwise.
    """
    logger.setLevel(logging.DEBUG if is_debug() else logging.INFO)
