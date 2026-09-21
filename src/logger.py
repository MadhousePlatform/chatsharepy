"""
logger.py
Configures the shared application logger. Log records are formatted with
monolog-python's Monolog-compatible JSON formatter and sent to syslog, so
they can be read by Laravel on the panel.
"""

import logging
import os
import sys

from monolog import MonologHandler

from src.debug import is_debug

# The local syslog daemon (rsyslog/syslog-ng/journald) listens on this Unix
# domain socket on a typical Linux host, which is how this app is deployed
# (see chatshare.service). MonologHandler defaults to a UDP socket at
# localhost:514, which nothing is listening on in production, so records
# would be silently dropped. Point it at the real local syslog socket
# instead, overridable via SYSLOG_ADDRESS for local dev/testing on
# platforms where /dev/log doesn't exist.
SYSLOG_ADDRESS = os.getenv("SYSLOG_ADDRESS", "/dev/log")

CONSOLE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logger = logging.getLogger("chatshare")
logger.addHandler(MonologHandler(address=SYSLOG_ADDRESS))


def _remove_console_handlers() -> None:
    """Detach any console handler a previous configure_logger() call added."""
    for handler in list(logger.handlers):
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, MonologHandler):
            logger.removeHandler(handler)


def configure_logger() -> None:
    """
    Set the logger's level from the current debug state, and mirror
    records to the console (stdout) while debug mode is enabled.

    Call this after parse_args() has run, so is_debug() reflects the
    --debug flag: DEBUG level when debug mode is enabled, INFO otherwise.
    The syslog handler is unaffected by debug state and stays attached
    either way.
    """
    logger.setLevel(logging.DEBUG if is_debug() else logging.INFO)

    _remove_console_handlers()

    if is_debug():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
        logger.addHandler(console_handler)
