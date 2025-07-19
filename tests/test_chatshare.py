#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import sys
import unittest
from unittest.mock import Mock, patch
from io import StringIO
from src.chatshare import main

class TestChatshare(unittest.TestCase):
    """
    Tests for the Chatshare application.
    """

    @patch('src.chatshare.DiscordClient')
    def test_main_output(self, mock_discord_client):
        """Test that main() prints 'Welcome to Chatshare!' and mocks DiscordClient"""

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
            self.assertEqual(output, "Welcome to Chatshare!")
            # Assert DiscordClient was instantiated and run was called
            mock_discord_client.assert_called_once()
            mock_instance.run.assert_called_once()
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()
