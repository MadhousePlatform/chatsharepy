#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import os
import unittest
from unittest.mock import Mock, patch
from src.chatshare import main


class TestChatshareEnvLoading(unittest.TestCase):
    """
    Tests that .env loading is delegated to pyauto-dotenv rather than an
    explicit load_dotenv() call in application code.
    """

    def test_pyauto_dotenv_is_a_declared_dependency(self):
        requirements_path = os.path.join(
            os.path.dirname(__file__), '..', 'requirements.txt')
        with open(requirements_path, encoding='utf-8') as requirements_file:
            requirements = requirements_file.read()

        self.assertIn('pyauto-dotenv', requirements)

    def test_module_does_not_call_load_dotenv_explicitly(self):
        import src.chatshare as chatshare  # pylint: disable=import-outside-toplevel

        self.assertFalse(hasattr(chatshare, 'load_dotenv'))


class TestChatshare(unittest.TestCase):
    """
    Tests for the Chatshare application.
    """

    @patch('src.chatshare.logger')
    @patch('src.chatshare.Pelican')
    @patch('src.chatshare.parse_args')
    @patch('src.chatshare.DiscordClient')
    def test_main_output(self, mock_discord_client, mock_parse_args, mock_pelican, mock_logger):
        """Test that main() logs 'Chatshare starting' at INFO and mocks DiscordClient"""
        mock_pelican.return_value.get_servers.return_value = []

        # Mock the run method so it doesn't actually try to connect
        mock_instance = mock_discord_client.return_value
        mock_instance.run = Mock()

        # Call the main function
        main()

        # Assert the expected log message
        mock_logger.info.assert_called_once_with("Chatshare starting")
        # Assert DiscordClient was instantiated and run was called
        mock_parse_args.assert_called_once()
        mock_pelican.assert_called_once()
        mock_discord_client.assert_called_once()
        mock_instance.run.assert_called_once()

    @patch('src.chatshare.logger')
    @patch('src.chatshare.Websockets')
    @patch('src.chatshare.Pelican')
    @patch('src.chatshare.parse_args')
    @patch('src.chatshare.DiscordClient')
    def test_main_with_servers(
            self, mock_discord_client, mock_parse_args, mock_pelican, mock_websockets,
            mock_logger):
        """Test that main() connects to servers returned by Pelican"""
        server = {'external_id': 'srv1', 'name': 'Server 1', 'description': 'Main Server'}
        mock_pelican.return_value.get_servers.return_value = [server]

        mock_instance = mock_discord_client.return_value
        mock_instance.run = Mock()
        mock_ws_instance = mock_websockets.return_value

        main()

        # Render each logged call the way the logging module would, so the
        # assertion covers both the plain message and the lazily-formatted
        # "server: %s - %s - %s" call.
        rendered_messages = [
            call.args[0] % call.args[1:] if call.args[1:] else call.args[0]
            for call in mock_logger.info.call_args_list
        ]
        self.assertIn("Chatshare starting", rendered_messages)
        self.assertIn("server: srv1 - Server 1 - Main Server", rendered_messages)
        mock_websockets.assert_called_once_with(server)
        mock_ws_instance.connect_to_server.assert_called_once_with(server)

if __name__ == '__main__':
    unittest.main()
