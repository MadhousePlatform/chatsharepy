import json
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

    @patch('src.websockets.websocket.WebSocketApp')
    @patch('src.websockets.requests.get')
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com',
        'PANEL_WSS_URL': 'wss://example.com',
        'WINGS_TOKEN': 'dummy_wings_token',
        'PANEL_ORIGIN_URL': 'https://example.com',
    })
    def test_console_output_with_empty_args_does_not_raise(self, mock_get, mock_websocket_app):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'token': 'abc123'}}
        mock_get.return_value = mock_response

        server = {'external_id': 'srv_ext_id', 'identifier': 'srv_id', 'uuid': 'srv_uuid'}
        self.ws.connect_to_server(server)

        on_message = mock_websocket_app.call_args.kwargs['on_message']
        empty_args_frame = json.dumps({"event": "console output", "args": []})

        # Must not raise IndexError: an empty-args frame should be ignored.
        on_message(Mock(), empty_args_frame)

    @patch('src.websockets.websocket.WebSocketApp')
    @patch('src.websockets.requests.get')
    @patch.dict(os.environ, {
        'PANEL_CLIENT_KEY': 'dummy_key',
        'PANEL_API_URL': 'https://example.com',
        'PANEL_WSS_URL': 'wss://example.com',
        'WINGS_TOKEN': 'dummy_wings_token',
        'PANEL_ORIGIN_URL': 'https://example.com',
    })
    @patch('src.websockets.parse_output')
    def test_console_output_with_single_arg_parses_output(
            self, mock_parse_output, mock_get, mock_websocket_app):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'token': 'abc123'}}
        mock_get.return_value = mock_response

        server = {'external_id': 'srv_ext_id', 'identifier': 'srv_id', 'uuid': 'srv_uuid'}
        self.ws.connect_to_server(server)

        on_message = mock_websocket_app.call_args.kwargs['on_message']
        single_arg_frame = json.dumps({"event": "console output", "args": ["hello world"]})

        on_message(Mock(), single_arg_frame)

        mock_parse_output.assert_called_once_with("[srv_ext_id] hello world", server)
