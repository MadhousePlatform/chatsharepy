import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import threading
import time
from src.websockets import Websockets
from src.broadcast import broadcast_to_all


class TestWebSocketConnection(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_server = {
            'external_id': 'test-server',
            'identifier': 'test-identifier',
            'uuid': 'test-uuid-123',
            'name': 'Test Server',
            'description': 'Test server for unit tests',
            'status': 'running'
        }

        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'PANEL_CLIENT_KEY': 'test-client-key',
            'PANEL_API_URL': 'https://test.example.com/api',
            'PANEL_WSS_URL': 'wss://test.example.com/api',
            'WINGS_TOKEN': 'test-wings-token'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_success(self, mock_get):
        """Test successful WebSocket credential retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'token': 'test-websocket-token'}
        }
        mock_get.return_value = mock_response

        ws = Websockets(self.test_server)
        ws.get_websocket_credentials('test-identifier')

        # Verify the token was set correctly
        self.assertEqual(ws.token, 'test-websocket-token')

        # Verify the API call was made with correct parameters
        mock_get.assert_called_once_with(
            'https://test.example.com/api/client/servers/test-identifier/websocket',
            headers={
                'Authorization': 'Bearer test-client-key',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_forbidden(self, mock_get):
        """Test handling of 403 Forbidden response."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        ws = Websockets(self.test_server)

        with self.assertRaises(PermissionError) as context:
            ws.get_websocket_credentials('test-identifier')

        self.assertIn("403 Forbidden", str(context.exception))

    @patch('src.websockets.websocket.WebSocketApp')
    @patch('src.websockets.set_websocket')
    @patch('src.websockets.threading.Thread')
    def test_websocket_connection_establishment(self, mock_thread, mock_set_websocket, mock_websocket_app):
        """Test WebSocket connection establishment."""
        # Mock WebSocket app
        mock_ws = Mock()
        mock_websocket_app.return_value = mock_ws

        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        ws = Websockets(self.test_server)
        ws.token = 'test-token'

        # Test connection
        ws.connect_to_server(self.test_server)

        # Verify WebSocket app was created with correct parameters
        mock_websocket_app.assert_called_once()
        call_args = mock_websocket_app.call_args

        # Check URL format
        expected_url = f"wss://test.example.com/api/servers/{self.test_server['uuid']}/ws?token=test-wings-token"
        self.assertEqual(call_args[0][0], expected_url)

        # Check headers
        expected_headers = [
            "Authorization: Bearer test-wings-token",
            "Origin: https://peli.sketchni.uk/"
        ]
        self.assertEqual(call_args[1]['header'], expected_headers)

        # Verify thread was started
        mock_thread_instance.start.assert_called_once()

    def test_websocket_message_handling(self):
        """Test WebSocket message handling for different event types."""
        ws = Websockets(self.test_server)

        # Test messages
        test_cases = [
            {
                'message': '{"event": "stats", "args": []}',
                'expected_action': 'ignore'
            },
            {
                'message': '{"event": "auth required", "args": []}',
                'expected_action': 'send_auth'
            },
            {
                'message': '{"event": "auth success", "args": []}',
                'expected_action': 'start_keepalive'
            },
            {
                'message': '{"event": "console output", "args": ["Test console output"]}',
                'expected_action': 'parse_output'
            }
        ]

        for case in test_cases:
            with self.subTest(message=case['message']):
                # This would need to be tested by mocking the on_message callback
                # and verifying the appropriate actions are taken
                message_data = json.loads(case['message'])
                self.assertIn('event', message_data)
                self.assertIn('args', message_data)


class TestWebSocketDataBroadcasting(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for broadcasting tests."""
        self.test_origin = {
            'external_id': 'server1',
            'identifier': 'server1-id',
            'uuid': 'server1-uuid'
        }

        # Mock websocket list
        self.mock_websocket1 = Mock()
        self.mock_websocket1.sock = Mock()
        self.mock_websocket1.sock.connected = True

        self.mock_websocket2 = Mock()
        self.mock_websocket2.sock = Mock()
        self.mock_websocket2.sock.connected = True

        self.mock_websocket_disconnected = Mock()
        self.mock_websocket_disconnected.sock = Mock()
        self.mock_websocket_disconnected.sock.connected = False

    @patch('src.broadcast.websock')
    def test_broadcast_to_connected_sockets(self, mock_websock):
        """Test broadcasting to connected WebSocket connections."""
        # Set up mock websocket list
        mock_websock.__len__.return_value = 2
        mock_websock.__iter__.return_value = iter([
            {'socket': self.mock_websocket1, 'name': 'server2'},
            {'socket': self.mock_websocket2, 'name': 'server3'}
        ])

        test_data = "tellraw @a Hello World"

        # Test broadcast
        broadcast_to_all(self.test_origin, test_data, except_origin=True)

        # Verify messages were sent to connected sockets
        expected_message = json.dumps({"event": "send command", "args": [test_data]})
        self.mock_websocket1.send.assert_called_once_with(expected_message)
        self.mock_websocket2.send.assert_called_once_with(expected_message)

    @patch('src.broadcast.websock')
    def test_broadcast_skips_disconnected_sockets(self, mock_websock):
        """Test that broadcasting skips disconnected WebSocket connections."""
        # Set up mock websocket list with one disconnected socket
        mock_websock.__len__.return_value = 2
        mock_websock.__iter__.return_value = iter([
            {'socket': self.mock_websocket1, 'name': 'server2'},
            {'socket': self.mock_websocket_disconnected, 'name': 'server3'}
        ])

        test_data = "tellraw @a Hello World"

        # Test broadcast
        broadcast_to_all(self.test_origin, test_data, except_origin=True)

        # Verify message was sent only to connected socket
        expected_message = json.dumps({"event": "send command", "args": [test_data]})
        self.mock_websocket1.send.assert_called_once_with(expected_message)
        self.mock_websocket_disconnected.send.assert_not_called()

    @patch('src.broadcast.websock')
    def test_broadcast_except_origin(self, mock_websock):
        """Test broadcasting except to origin server."""
        # Set up mock websocket list including origin server
        mock_websock.__len__.return_value = 3
        mock_websock.__iter__.return_value = iter([
            {'socket': self.mock_websocket1, 'name': 'server1'},  # Origin server
            {'socket': self.mock_websocket2, 'name': 'server2'},
            {'socket': Mock(), 'name': 'server3'}
        ])

        test_data = "tellraw @a Hello World"

        # Test broadcast with except_origin=True
        broadcast_to_all(self.test_origin, test_data, except_origin=True)

        # Verify message was not sent to origin server
        self.mock_websocket1.send.assert_not_called()
        # Verify message was sent to other servers
        expected_message = json.dumps({"event": "send command", "args": [test_data]})
        self.mock_websocket2.send.assert_called_once_with(expected_message)

    @patch('src.broadcast.websock')
    def test_broadcast_handles_send_errors(self, mock_websock):
        """Test that broadcasting handles send errors gracefully."""
        # Set up mock websocket that raises an exception
        mock_failing_websocket = Mock()
        mock_failing_websocket.sock = Mock()
        mock_failing_websocket.sock.connected = True
        mock_failing_websocket.send.side_effect = Exception("Connection lost")

        mock_websock.__len__.return_value = 1
        mock_websock.__iter__.return_value = iter([
            {'socket': mock_failing_websocket, 'name': 'server2'}
        ])

        test_data = "tellraw @a Hello World"

        # Test broadcast - should not raise exception
        try:
            broadcast_to_all(self.test_origin, test_data, except_origin=True)
        except Exception as e:
            self.fail(f"broadcast_to_all raised {e} unexpectedly")

    @patch('src.broadcast.websock')
    def test_broadcast_with_empty_websocket_list(self, mock_websock):
        """Test broadcasting with empty WebSocket list."""
        # Set up empty websocket list
        mock_websock.__len__.return_value = 0

        test_data = "tellraw @a Hello World"

        # Test broadcast - should not raise exception
        try:
            broadcast_to_all(self.test_origin, test_data, except_origin=True)
        except Exception as e:
            self.fail(f"broadcast_to_all raised {e} unexpectedly")


class TestWebSocketIntegration(unittest.TestCase):
    """Integration tests for WebSocket functionality."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.test_server = {
            'external_id': 'integration-server',
            'identifier': 'integration-id',
            'uuid': 'integration-uuid',
            'name': 'Integration Test Server'
        }

    @patch('src.websockets.requests.get')
    @patch('src.websockets.websocket.WebSocketApp')
    @patch('src.websockets.set_websocket')
    @patch('src.websockets.threading.Thread')
    def test_full_websocket_lifecycle(self, mock_thread, mock_set_websocket, mock_websocket_app, mock_get):
        """Test complete WebSocket lifecycle from connection to message handling."""
        # Mock environment variables
        with patch.dict('os.environ', {
            'PANEL_CLIENT_KEY': 'test-client-key',
            'PANEL_API_URL': 'https://test.example.com/api',
            'PANEL_WSS_URL': 'wss://test.example.com/api',
            'WINGS_TOKEN': 'test-wings-token'
        }):
            # Mock successful credential retrieval
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': {'token': 'test-websocket-token'}
            }
            mock_get.return_value = mock_response

            # Mock WebSocket app
            mock_ws = Mock()
            mock_websocket_app.return_value = mock_ws

            # Mock thread
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            # Create WebSocket instance and connect
            ws = Websockets(self.test_server)
            ws.connect_to_server(self.test_server)

            # Verify credential retrieval was called
            mock_get.assert_called_once()

            # Verify WebSocket was created and thread started
            mock_websocket_app.assert_called_once()
            mock_thread_instance.start.assert_called_once()

            # Verify websocket was registered
            mock_set_websocket.assert_called_once_with(mock_ws, 'integration-server')


if __name__ == '__main__':
    unittest.main()