"""
Tests for src/broadcast.py
"""
import threading
import time
import unittest
from unittest.mock import Mock, patch

from src import broadcast
from src.broadcast import broadcast_to_all, set_websocket, unset_websocket


class TestBroadcastToAll(unittest.TestCase):
    """Tests for broadcast_to_all."""

    def setUp(self):
        """Ensure the module-level websocket list starts empty for each test."""
        broadcast.websock = []

    def tearDown(self):
        """Leave the module-level websocket list clean for other test modules."""
        broadcast.websock = []

    def _add_connected_socket(self, name):
        mock_socket = Mock()
        mock_socket.sock.connected = True
        set_websocket(mock_socket, name)
        return mock_socket

    @patch('src.broadcast.discord_client')
    def test_relays_to_discord_by_default(self, mock_discord_client):
        """A Minecraft-sourced message should still reach Discord."""
        self._add_connected_socket('vanilla')

        broadcast_to_all({'external_id': 'other'}, 'data', 'message', except_origin=True)

        mock_discord_client.discord_c.send_message.assert_called_once_with('message')

    @patch('src.broadcast.discord_client')
    def test_does_not_relay_to_discord_when_message_originated_there(self, mock_discord_client):
        """
        A Discord-originated message must not be echoed straight back to
        Discord by the bot.
        """
        self._add_connected_socket('vanilla')

        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )

        mock_discord_client.discord_c.send_message.assert_not_called()

    @patch('src.broadcast.discord_client')
    def test_still_sends_to_minecraft_sockets_when_discord_relay_skipped(self, mock_discord_client):
        """Skipping the Discord relay must not stop the message reaching Minecraft."""
        mock_socket = self._add_connected_socket('vanilla')

        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )

        # The Minecraft send happens on a background thread; give it a
        # moment to run.
        for _ in range(50):
            if mock_socket.send.called:
                break
            time.sleep(0.01)

        mock_discord_client.discord_c.send_message.assert_not_called()
        mock_socket.send.assert_called_once()

    @patch('src.broadcast.discord_client')
    def test_minecraft_send_does_not_block_caller(self, mock_discord_client):
        """
        The socket send loop must run off the calling thread so a slow
        Minecraft socket cannot stall the caller (e.g. the Discord gateway
        event loop).
        """
        mock_socket = self._add_connected_socket('vanilla')
        release_event = threading.Event()

        def slow_send(_payload):
            # Block until released, simulating a stalled Minecraft socket.
            release_event.wait(timeout=2)

        mock_socket.send.side_effect = slow_send

        started = time.monotonic()
        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )
        elapsed = time.monotonic() - started

        release_event.set()
        self.assertLess(elapsed, 0.5)
        _ = mock_discord_client

    def test_unset_websocket_removes_entry(self):
        mock_socket = self._add_connected_socket('vanilla')
        unset_websocket(mock_socket)
        self.assertEqual(broadcast.websock, [])


if __name__ == '__main__':
    unittest.main()
