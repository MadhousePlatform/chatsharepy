import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from src.pelican_manager import Pelican


class TestPelicanIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for Pelican integration tests."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'PANEL_APPLICATION_KEY': 'test-app-key',
            'PANEL_CLIENT_KEY': 'test-client-key',
            'PANEL_API_URL': 'https://test.example.com/api'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('src.pelican_manager.requests.get')
    def test_get_servers_success(self, mock_get):
        """Test successful retrieval of server list."""
        # Mock application API response
        app_response = Mock()
        app_response.text = json.dumps({
            'data': [
                {
                    'attributes': {
                        'external_id': 'server1',
                        'uuid': 'uuid-1',
                        'identifier': 'server1-id',
                        'name': 'Server 1',
                        'description': 'First test server'
                    }
                },
                {
                    'attributes': {
                        'external_id': 'server2',
                        'uuid': 'uuid-2',
                        'identifier': 'server2-id',
                        'name': 'Server 2',
                        'description': 'Second test server'
                    }
                }
            ]
        })
        
        # Mock client API responses for status
        client_response1 = Mock()
        client_response1.status_code = 200
        client_response1.text = json.dumps({
            'attributes': {
                'current_state': 'running'
            }
        })
        
        client_response2 = Mock()
        client_response2.status_code = 200
        client_response2.text = json.dumps({
            'attributes': {
                'current_state': 'stopped'
            }
        })
        
        # Configure mock to return different responses for different calls
        mock_get.side_effect = [app_response, client_response1, client_response2]
        
        pelican = Pelican()
        servers = pelican.get_servers()
        
        # Verify the results
        self.assertEqual(len(servers), 2)
        
        # Check first server
        self.assertEqual(servers[0]['external_id'], 'server1')
        self.assertEqual(servers[0]['uuid'], 'uuid-1')
        self.assertEqual(servers[0]['identifier'], 'server1-id')
        self.assertEqual(servers[0]['name'], 'Server 1')
        self.assertEqual(servers[0]['description'], 'First test server')
        self.assertEqual(servers[0]['status'], 'running')
        
        # Check second server
        self.assertEqual(servers[1]['external_id'], 'server2')
        self.assertEqual(servers[1]['status'], 'stopped')
        
        # Verify API calls were made with correct headers
        self.assertEqual(mock_get.call_count, 3)
        
        # Check application API call
        app_call = mock_get.call_args_list[0]
        self.assertEqual(app_call[0][0], 'https://test.example.com/api/application/servers')
        self.assertEqual(app_call[1]['headers']['Authorization'], 'Bearer test-app-key')
        
        # Check client API calls
        client_call1 = mock_get.call_args_list[1]
        self.assertEqual(client_call1[0][0], 'https://test.example.com/api/client/servers/server1-id/resources')
        self.assertEqual(client_call1[1]['headers']['Authorization'], 'Bearer test-client-key')

    @patch('src.pelican_manager.requests.get')
    def test_get_servers_client_api_failure(self, mock_get):
        """Test handling of client API failures when getting server status."""
        # Mock application API response
        app_response = Mock()
        app_response.text = json.dumps({
            'data': [
                {
                    'attributes': {
                        'external_id': 'server1',
                        'uuid': 'uuid-1',
                        'identifier': 'server1-id',
                        'name': 'Server 1',
                        'description': 'First test server'
                    }
                }
            ]
        })
        
        # Mock client API failure
        client_response = Mock()
        client_response.status_code = 403
        client_response.text = '{"error": "Forbidden"}'
        
        mock_get.side_effect = [app_response, client_response]
        
        pelican = Pelican()
        servers = pelican.get_servers()
        
        # Verify server was still included with default status
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['external_id'], 'server1')
        self.assertEqual(servers[0]['status'], 'unavailable')  # Default status

    @patch('src.pelican_manager.requests.get')
    def test_get_servers_exception_handling(self, mock_get):
        """Test exception handling in get_servers method."""
        # Mock application API response
        app_response = Mock()
        app_response.text = json.dumps({
            'data': [
                {
                    'attributes': {
                        'external_id': 'server1',
                        'uuid': 'uuid-1',
                        'identifier': 'server1-id',
                        'name': 'Server 1',
                        'description': 'First test server'
                    }
                }
            ]
        })
        
        # Mock client API to raise exception
        def side_effect(*args, **kwargs):
            if 'application/servers' in args[0]:
                return app_response
            else:
                raise Exception("Network error")
        
        mock_get.side_effect = side_effect
        
        pelican = Pelican()
        servers = pelican.get_servers()
        
        # Verify server was still included with default status
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]['external_id'], 'server1')
        self.assertEqual(servers[0]['status'], 'unavailable')  # Default status due to exception

    @patch('src.pelican_manager.requests.get')
    def test_get_servers_empty_response(self, mock_get):
        """Test handling of empty server list response."""
        # Mock empty application API response
        app_response = Mock()
        app_response.text = json.dumps({'data': []})
        
        mock_get.return_value = app_response
        
        pelican = Pelican()
        servers = pelican.get_servers()
        
        # Verify empty list is returned
        self.assertEqual(len(servers), 0)
        self.assertEqual(servers, [])

    @patch('src.pelican_manager.requests.get')
    def test_get_servers_malformed_json(self, mock_get):
        """Test handling of malformed JSON responses."""
        # Mock malformed application API response
        app_response = Mock()
        app_response.text = "invalid json"
        
        mock_get.return_value = app_response
        
        pelican = Pelican()
        
        # This should raise an exception due to malformed JSON
        with self.assertRaises(json.JSONDecodeError):
            pelican.get_servers()


class TestPelicanWebSocketIntegration(unittest.TestCase):
    """Integration tests for Pelican and WebSocket functionality."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.env_patcher = patch.dict('os.environ', {
            'PANEL_APPLICATION_KEY': 'test-app-key',
            'PANEL_CLIENT_KEY': 'test-client-key',
            'PANEL_API_URL': 'https://test.example.com/api',
            'PANEL_WSS_URL': 'wss://test.example.com/api',
            'WINGS_TOKEN': 'test-wings-token'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('src.pelican_manager.requests.get')
    @patch('src.websockets.Websockets')
    def test_pelican_websocket_integration(self, mock_websockets, mock_get):
        """Test integration between Pelican server management and WebSocket connections."""
        # Mock Pelican API response
        app_response = Mock()
        app_response.text = json.dumps({
            'data': [
                {
                    'attributes': {
                        'external_id': 'gameserver',
                        'uuid': 'game-uuid',
                        'identifier': 'game-id',
                        'name': 'Game Server',
                        'description': 'Main game server'
                    }
                }
            ]
        })
        
        client_response = Mock()
        client_response.status_code = 200
        client_response.text = json.dumps({
            'attributes': {
                'current_state': 'running'
            }
        })
        
        mock_get.side_effect = [app_response, client_response]
        
        # Mock WebSocket instance
        mock_ws_instance = Mock()
        mock_ws_instance.origin = 'gameserver'  # Set the expected return value
        mock_websockets.return_value = mock_ws_instance
        
        # Get servers from Pelican
        pelican = Pelican()
        servers = pelican.get_servers()
        
        # Verify server was retrieved
        self.assertEqual(len(servers), 1)
        server = servers[0]
        self.assertEqual(server['external_id'], 'gameserver')
        self.assertEqual(server['status'], 'running')
        
        # Use the mocked WebSocket
        from src.websockets import Websockets
        ws = Websockets(server)
        
        # Verify WebSocket was initialized with correct server
        mock_websockets.assert_called_once_with(server)
        self.assertEqual(ws.origin, 'gameserver')


if __name__ == '__main__':
    unittest.main()