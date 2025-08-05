import unittest
from unittest.mock import patch, Mock
from requests.exceptions import ConnectionError, RequestException
import os

from src.websockets import Websockets  # Adjust import based on your structure


class TestWebsockets(unittest.TestCase):

    def setUp(self):
        self.server = {'external_id': 'srv_ext_id', 'identifier': 'srv_id'}
        self.ws = Websockets(self.server)

    @patch('requests.get')
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com'
    })
    def test_get_websocket_credentials_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'token': 'abc123'}}
        mock_get.return_value = mock_response

        self.ws.get_websocket_credentials('srv_id')

        self.assertEqual(self.ws.token, 'abc123')
        mock_get.assert_called_once()

    @patch('requests.get')
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com'
    })
    def test_get_websocket_credentials_403_forbidden(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with self.assertRaises(PermissionError) as context:
            self.ws.get_websocket_credentials('srv_id')

        self.assertIn("403 Forbidden", str(context.exception))

    @patch('requests.get', side_effect=ConnectionError)
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com'
    })
    def test_get_websocket_credentials_connection_error(self, mock_get):
        with self.assertRaises(RequestException) as context:
            self.ws.get_websocket_credentials('srv_id')

        self.assertEqual(str(context.exception), "Connection error while fetching websocket credentials")

    @patch('requests.get', side_effect=RequestException)
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com'
    })
    def test_get_websocket_credentials_request_exception(self, mock_get):
        with self.assertRaises(RequestException) as context:
            self.ws.get_websocket_credentials('srv_id')

        self.assertIn("Connection error while fetching", str(context.exception))
