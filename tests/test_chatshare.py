#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import importlib
import sys
import unittest
from unittest.mock import Mock, patch
from io import StringIO
from src.chatshare import main


class TestChatshareEnvLoading(unittest.TestCase):
    """
    Tests that Chatshare loads a .env file before checking required env vars.
    """

    def test_module_calls_load_dotenv_before_required_env_check(self):
        import src.chatshare as chatshare  # pylint: disable=import-outside-toplevel

        with patch('dotenv.load_dotenv') as mock_load_dotenv:
            importlib.reload(chatshare)

        mock_load_dotenv.assert_called_once()

        # Restore the module to its normal (non-mocked) state for other tests.
        importlib.reload(chatshare)


class TestChatshare(unittest.TestCase):
    """
    Tests for the Chatshare application.
    """

    @patch('src.chatshare.Pelican')
    @patch('src.chatshare.parse_args')
    @patch('src.chatshare.DiscordClient')
    def test_main_output(self, mock_discord_client, mock_parse_args, mock_pelican):
        """Test that main() prints 'Chatshare starting' and mocks DiscordClient"""
        mock_pelican.return_value.get_servers.return_value = []

        # Mock the run method so it doesn't actually try to connect
        mock_instance = mock_discord_client.return_value
        mock_instance.run = Mock()

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output
            self.assertEqual(output, "Chatshare starting")
            # Assert DiscordClient was instantiated and run was called
            mock_parse_args.assert_called_once()
            mock_pelican.assert_called_once()
            mock_discord_client.assert_called_once()
            mock_instance.run.assert_called_once()
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

    @patch('src.chatshare.Websockets')
    @patch('src.chatshare.Pelican')
    @patch('src.chatshare.parse_args')
    @patch('src.chatshare.DiscordClient')
    def test_main_with_servers(self, mock_discord_client, mock_parse_args, mock_pelican, mock_websockets):
        """Test that main() connects to servers returned by Pelican"""
        server = {'external_id': 'srv1', 'name': 'Server 1', 'description': 'Main Server'}
        mock_pelican.return_value.get_servers.return_value = [server]

        mock_instance = mock_discord_client.return_value
        mock_instance.run = Mock()
        mock_ws_instance = mock_websockets.return_value

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            main()
            output = captured_output.getvalue().strip()
            self.assertIn("Chatshare starting", output)
            self.assertIn("server: srv1 - Server 1 - Main Server", output)
            mock_websockets.assert_called_once_with(server)
            mock_ws_instance.connect_to_server.assert_called_once_with(server)
        finally:
            sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()
