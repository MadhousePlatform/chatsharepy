#!/usr/bin/env python3

"""
Tests for the DiscordClient class in discord.py.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.discord_client import DiscordClient
from src.events import EventEmitter


class TestDiscordClient(unittest.TestCase):
    """
    Tests for the DiscordClient class.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.event_emitter = EventEmitter()

    @patch('discord.Client.__init__')
    def test_init_with_different_channel_id(self, mock_super_init):
        """Test DiscordClient initialization with different channel ID."""
        mock_super_init.return_value = None

        client = DiscordClient(self.event_emitter, 987654321)

        self.assertEqual(client.watch_channel_id, 987654321)

    @patch('discord.Client.__init__')
    def test_on_message_wrong_channel(self, mock_super_init):
        """Test on_message method with message from wrong channel."""
        mock_super_init.return_value = None

        client = DiscordClient(self.event_emitter, 123456789)

        # Create mock message from different channel
        mock_message = Mock()
        mock_message.channel.id = 987654321  # Different channel
        mock_message.author = Mock()
        mock_message.content = 'Hello, world!'

        # Mock the event emitter emit method
        with patch.object(self.event_emitter, 'emit') as mock_emit:
            asyncio.run(client.on_message(mock_message))

            # Should not emit any events
            mock_emit.assert_not_called()

    @patch('discord.Client.__init__')
    def test_on_chat_message_from_discord(self, mock_super_init):
        """Test on_chat_message method with Discord source (should not forward)."""
        mock_super_init.return_value = None

        client = DiscordClient(self.event_emitter, 123456789)
        mock_channel = AsyncMock()
        client.watch_channel = mock_channel

        message = {
            'message': 'Hello from Discord',
            'sender': 'DiscordUser',
            'source': 'discord'
        }

        asyncio.run(client.on_chat_message(message))
        mock_channel.send.assert_not_called()

    @patch('discord.Client.__init__')
    def test_on_chat_message_from_other_source(self, mock_super_init):
        """Test on_chat_message method with non-Discord source (should forward)."""
        mock_super_init.return_value = None

        client = DiscordClient(self.event_emitter, 123456789)

        # Mock the watch channel
        mock_channel = AsyncMock()
        client.watch_channel = mock_channel

        message = {
            'message': 'Hello from Slack',
            'sender': 'SlackUser',
            'source': 'slack'
        }

        asyncio.run(client.on_chat_message(message))
        mock_channel.send.assert_called_once_with(
            "[slack] <SlackUser> Hello from Slack"
        )

    @patch('discord.Client.__init__')
    def test_message_formatting(self, mock_super_init):
        """Test that message formatting works correctly."""
        mock_super_init.return_value = None

        client = DiscordClient(self.event_emitter, 123456789)

        # Mock the watch channel
        mock_channel = AsyncMock()
        client.watch_channel = mock_channel

        # Test different message formats
        test_cases = [
            {
                'input': {'message': 'Test message', 'sender': 'User1', 'source': 'slack'},
                'expected': '[slack] <User1> Test message'
            },
            {
                'input': {'message': 'Another message', 'sender': 'User2', 'source': 'telegram'},
                'expected': '[telegram] <User2> Another message'
            },
            {
                'input': {'message': 'Special chars!@#', 'sender': 'User3', 'source': 'irc'},
                'expected': '[irc] <User3> Special chars!@#'
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                mock_channel.reset_mock()

                with patch('builtins.print'):
                    asyncio.run(client.on_chat_message(test_case['input']))

                mock_channel.send.assert_called_once_with(test_case['expected'])

if __name__ == '__main__':
    unittest.main()
