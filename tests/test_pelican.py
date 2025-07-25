import unittest
import json
import os
from unittest.mock import patch, MagicMock

from src.pelican_manager import Pelican

class TestPelicanGetServers(unittest.TestCase):
    def setUp(self):
        self.pelican = Pelican()
        # Set essential environment variables for the test
        os.environ["PANEL_APPLICATION_KEY"] = "test_app_key"
        os.environ["PANEL_CLIENT_KEY"] = "test_client_key"
        os.environ["PANEL_API_URL"] = "https://mock.api"

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_success(self, mock_get):
        # Simulate 1st GET call (list servers)
        app_servers_data = {
            "data": [
                {
                    "attributes": {
                        "external_id": "srv01",
                        "uuid": "uuid-1",
                        "identifier": "id1",
                        "name": "Alpha",
                        "description": "First",
                    }
                },
                {
                    "attributes": {
                        "external_id": "srv02",
                        "uuid": "uuid-2",
                        "identifier": "id2",
                        "name": "Beta",
                        "description": "Second",
                    }
                },
            ]
        }
        app_resp = MagicMock()
        app_resp.text = json.dumps(app_servers_data)

        # Simulate 2nd GET for server 1 resources
        resources_1 = MagicMock()
        resources_1.status_code = 200
        resources_1.text = json.dumps({"attributes": {"current_state": "online"}})

        # Simulate 3rd GET for server 2 resources
        resources_2 = MagicMock()
        resources_2.status_code = 200
        resources_2.text = json.dumps({"attributes": {"current_state": "offline"}})

        mock_get.side_effect = [app_resp, resources_1, resources_2]

        result = self.pelican.get_servers()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["status"], "online")
        self.assertEqual(result[1]["status"], "offline")
        self.assertEqual(result[0]["name"], "Alpha")
        self.assertEqual(result[1]["name"], "Beta")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_status_response_empty(self, mock_get):
        # Server exists, server resources response empty body
        app_servers_data = {
            "data": [
                {
                    "attributes": {
                        "external_id": "srv01",
                        "uuid": "uuid-1",
                        "identifier": "id1",
                        "name": "Alpha",
                        "description": "First",
                    }
                }
            ]
        }
        app_resp = MagicMock()
        app_resp.text = json.dumps(app_servers_data)

        resource_resp = MagicMock()
        resource_resp.status_code = 200
        resource_resp.text = ""

        mock_get.side_effect = [app_resp, resource_resp]
        result = self.pelican.get_servers()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "unavailable")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_resource_http_error(self, mock_get):
        # Server exists; fetching status fails (non-200)
        app_servers_data = {
            "data": [
                {
                    "attributes": {
                        "external_id": "srv01",
                        "uuid": "uuid-1",
                        "identifier": "id1",
                        "name": "Alpha",
                        "description": "First",
                    }
                }
            ]
        }
        app_resp = MagicMock()
        app_resp.text = json.dumps(app_servers_data)

        resource_resp = MagicMock()
        resource_resp.status_code = 500
        resource_resp.text = "Internal Error"

        mock_get.side_effect = [app_resp, resource_resp]
        result = self.pelican.get_servers()
        self.assertEqual(result[0]["status"], "unavailable")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_resource_exception(self, mock_get):
        # Server exists; resource fetch raises exception
        app_servers_data = {
            "data": [
                {
                    "attributes": {
                        "external_id": "srv01",
                        "uuid": "uuid-1",
                        "identifier": "id1",
                        "name": "Alpha",
                        "description": "First",
                    }
                }
            ]
        }
        app_resp = MagicMock()
        app_resp.text = json.dumps(app_servers_data)

        # 2nd call (fetch resources) raises exception
        mock_get.side_effect = [app_resp, Exception("Boom")]
        result = self.pelican.get_servers()
        self.assertEqual(result[0]["status"], "unavailable")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_empty_list(self, mock_get):
        # No servers in application API response
        app_servers_data = {"data": []}
        app_resp = MagicMock()
        app_resp.text = json.dumps(app_servers_data)
        mock_get.return_value = app_resp

        result = self.pelican.get_servers()
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()