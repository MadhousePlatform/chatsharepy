import logging
import unittest

from monolog import MonologHandler

from src.debug import debug_state
from src.logger import configure_logger, logger


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

    def test_configure_logger_sets_debug_level_when_debug_mode_enabled(self):
        debug_state['enabled'] = True

        configure_logger()

        self.assertEqual(logger.level, logging.DEBUG)

    def test_configure_logger_sets_info_level_when_debug_mode_disabled(self):
        debug_state['enabled'] = False

        configure_logger()

        self.assertEqual(logger.level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
