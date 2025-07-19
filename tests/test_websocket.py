import unittest
from unittest.mock import patch, MagicMock
import os

from src.websockets import Websockets


class TestWebsockets(unittest.TestCase):
    def setUp(self):
        # Mock server dictionary used for websocket client
        self.mock_server = {
            'external_id': 'abc123',
            'identifier': 'serverid',
            'uuid': 'uuid-abc-123',
        }
        # Prepare environment variables
        os.environ['PANEL_CLIENT_KEY'] = 'testtoken'
        os.environ['PANEL_API_URL'] = 'https://mockapi.test'
        os.environ['PANEL_WSS_URL'] = 'wss://mockwss.test'
        os.environ['WINGS_TOKEN'] = 'wingstest'

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_success(self, mock_get):
        # Mock successful requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'token': 'jwt_token'}}
        mock_get.return_value = mock_response

        ws = Websockets(self.mock_server)
        ws.get_websocket_credentials('serverid')

        self.assertEqual(ws.token, 'jwt_token')
        mock_get.assert_called_once()
        # Confirm correct URL
        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.endswith('/client/servers/serverid/websocket'))

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_403(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        ws = Websockets(self.mock_server)
        with self.assertRaises(PermissionError):
            ws.get_websocket_credentials('serverid')

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_connection_error(self, mock_get):
        # Simulate network error
        from requests.exceptions import ConnectionError
        mock_get.side_effect = ConnectionError("Name or service not known")

        ws = Websockets(self.mock_server)
        with self.assertRaises(ConnectionError) as cm:
            ws.get_websocket_credentials('serverid', max_retries=2, backoff_factor=0)
        self.assertIn('DNS resolution failed', str(cm.exception))

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_request_exception(self, mock_get):
        # Simulate general request error
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Timeout")

        ws = Websockets(self.mock_server)
        with self.assertRaises(RequestException):
            ws.get_websocket_credentials('serverid', max_retries=2, backoff_factor=0)

    @patch('src.websockets.requests.get')
    def test_get_websocket_credentials_retries_then_success(self, mock_get):
        # Raise an exception first, then succeed
        from requests.exceptions import ConnectionError
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'token': 'retrytoken'}}
        mock_get.side_effect = [ConnectionError("Temporary fail"), mock_response]

        ws = Websockets(self.mock_server)
        ws.get_websocket_credentials('serverid', max_retries=2, backoff_factor=0)
        self.assertEqual(ws.token, 'retrytoken')
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
