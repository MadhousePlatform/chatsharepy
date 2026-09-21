import unittest
from unittest.mock import patch

from src.debug import debug_state
from src.minecraft import parse_output


class TestParseOutput(unittest.TestCase):
    def test_parse_output_regular_line(self):
        result = parse_output("[vanilla] [19:41:36] [Server thread/INFO]: <Sketch> Hello world!",
                              {"external_id": "vanilla"})
        # Assuming parse_output returns processed text if successful
        self.assertIsNotNone(result)
        self.assertIn("Hello world", result)

    def test_parse_output_empty_line(self):
        result = parse_output("", {"external_id": "vanilla"})
        self.assertFalse(result)  # Or adapt if your function behaves differently

    def test_parse_output_with_special_event(self):
        # If parse_output triggers something special for keywords
        result = parse_output("[vanilla] [19:19:02] [Server thread/INFO]: Player has made the advancement [dookie pie]!",
                              {"external_id": "vanilla"})
        self.assertIn("dookie pie", result)


class TestParseOutputLogging(unittest.TestCase):
    """
    Representative cases proving parse_output logs at the right level via
    the shared logger, rather than printing to stdout.
    """

    def setUp(self):
        self.original_debug_state = debug_state['enabled']
        debug_state['enabled'] = True

    def tearDown(self):
        debug_state['enabled'] = self.original_debug_state

    @patch("src.minecraft.logger")
    def test_invalid_server_object_logs_an_error(self, mock_logger):
        result = parse_output("some output", {"external_id": 123})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "Invalid server object", mock_logger.error.call_args.args[0])

    @patch("src.minecraft.logger")
    def test_unknown_server_logs_a_debug_message(self, mock_logger):
        result = parse_output("hello", {"external_id": "no-such-server"})

        self.assertIsNone(result)
        mock_logger.debug.assert_any_call(
            "No regexes found for server: %s", "no-such-server")


class TestParseOutputLoggingWithoutDebugMode(unittest.TestCase):
    """
    Error paths in parse_output must log unconditionally, not only when
    debug mode is enabled, so real error conditions still reach syslog in
    normal production operation.
    """

    def setUp(self):
        self.original_debug_state = debug_state['enabled']
        debug_state['enabled'] = False

    def tearDown(self):
        debug_state['enabled'] = self.original_debug_state

    @patch("src.minecraft.logger")
    def test_invalid_server_object_logs_an_error_without_debug_mode(self, mock_logger):
        result = parse_output("some output", {"external_id": 123})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "Invalid server object", mock_logger.error.call_args.args[0])

    @patch("src.minecraft.logger")
    def test_missing_external_id_logs_an_error_without_debug_mode(self, mock_logger):
        result = parse_output("some output", {"external_id": ""})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "external_id missing", mock_logger.error.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
