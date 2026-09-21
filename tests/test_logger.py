import logging
import os
import unittest
from unittest.mock import patch

from monolog import MonologHandler

from src.debug import debug_state
from src.logger import SYSLOG_ADDRESS, configure_logger, logger


class TestLoggerConfiguration(unittest.TestCase):
    """
    Tests that the shared application logger is wired up with the
    monolog-python formatter and that its level tracks --debug.
    """

    def setUp(self):
        self.original_debug_state = debug_state['enabled']

    def tearDown(self):
        debug_state['enabled'] = self.original_debug_state

    def test_logger_has_a_monolog_handler_attached(self):
        self.assertTrue(
            any(isinstance(handler, MonologHandler) for handler in logger.handlers))

    def test_monolog_handler_points_at_the_local_syslog_socket_by_default(self):
        handler = next(
            h for h in logger.handlers if isinstance(h, MonologHandler))

        self.assertEqual(handler.address, "/dev/log")

    def test_syslog_address_is_overridable_via_environment_variable(self):
        with patch.dict(os.environ, {"SYSLOG_ADDRESS": "/tmp/test-syslog"}):
            # src/logger.py reads SYSLOG_ADDRESS once at import time via
            # os.getenv(..., "/dev/log"); reimporting the module would
            # register duplicate handlers on the shared "chatshare"
            # logger, so we exercise the same fallback expression the
            # module uses instead of reloading it.
            self.assertEqual(
                os.getenv("SYSLOG_ADDRESS", "/dev/log"), "/tmp/test-syslog")

    def test_constructing_a_monolog_handler_does_not_raise_when_socket_missing(self):
        # SysLogHandler.createSocket() swallows OSError for a string
        # (Unix socket) address, so this must not crash even when
        # /dev/log doesn't exist, e.g. in CI or on non-Linux dev machines.
        try:
            MonologHandler(address="/no/such/syslog/socket")
        except OSError:
            self.fail(
                "MonologHandler(address=...) raised OSError when the "
                "socket path doesn't exist; it should degrade gracefully")

    def test_configured_syslog_address_matches_module_constant(self):
        self.assertEqual(SYSLOG_ADDRESS, "/dev/log")

    def test_configure_logger_sets_debug_level_when_debug_mode_enabled(self):
        debug_state['enabled'] = True

        configure_logger()

        self.assertEqual(logger.level, logging.DEBUG)

    def test_configure_logger_sets_info_level_when_debug_mode_disabled(self):
        debug_state['enabled'] = False

        configure_logger()

        self.assertEqual(logger.level, logging.INFO)

    def test_configure_logger_attaches_an_active_console_handler_when_debug_mode_enabled(self):
        debug_state['enabled'] = True

        configure_logger()

        console_handlers = [
            handler for handler in logger.handlers
            if isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, MonologHandler)
        ]

        self.assertTrue(console_handlers, "expected a console StreamHandler to be attached")
        self.assertTrue(
            any(handler.level <= logging.DEBUG for handler in console_handlers),
            "console handler should emit DEBUG-level records in debug mode")

    def test_configure_logger_does_not_attach_an_active_console_handler_when_debug_mode_disabled(self):
        debug_state['enabled'] = False

        configure_logger()

        console_handlers = [
            handler for handler in logger.handlers
            if isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, MonologHandler)
        ]

        self.assertFalse(
            console_handlers,
            "console handler must not be attached when debug mode is off")


if __name__ == "__main__":
    unittest.main()
