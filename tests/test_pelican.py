import unittest
import json
import os
from unittest.mock import patch, MagicMock

from src.pelican_manager import Pelican


class TestPelicanGetServers(unittest.TestCase):
    def setUp(self):
        self.pelican = Pelican()
        # Set essential environment variables for the test
        os.environ["PANEL_APPLICATION_KEY"] = "appkey"
        os.environ["PANEL_CLIENT_KEY"] = "clientkey"
        os.environ["PANEL_API_URL"] = "https://mock.api"

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_success(self, mock_get):
        # Mock first GET (application servers)
        mock_servers_data = {
            "data": [
                {"attributes": {
                    "external_id": "srv01",
                    "uuid": "u1",
                    "identifier": "i1",
                    "name": "Server 1",
                    "description": "The first server"
                }},
                {"attributes": {
                    "external_id": "srv02",
                    "uuid": "u2",
                    "identifier": "i2",
                    "name": "Server 2",
                    "description": "Second server"
                }},
            ]
        }
        app_resp = MagicMock()
        app_resp.text = json.dumps(mock_servers_data)
        # Resource response for each server
        resource1 = MagicMock()
        resource1.status_code = 200
        resource1.text = json.dumps({"attributes": {"current_state": "online"}})
        resource2 = MagicMock()
        resource2.status_code = 200
        resource2.text = json.dumps({"attributes": {"current_state": "offline"}})
        mock_get.side_effect = [app_resp, resource1, resource2]

        servers = self.pelican.get_servers()
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]["status"], "online")
        self.assertEqual(servers[1]["status"], "offline")
        self.assertEqual(servers[0]["name"], "Server 1")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_status_missing(self, mock_get):
        # Valid server, but no resources response body
        mock_servers_data = {"data": [{"attributes": {"identifier": "i1", "external_id": "srv01", "uuid": "u1",
                                                      "name": "n", "description": "desc"}}]}
        app_resp = MagicMock()
        app_resp.text = json.dumps(mock_servers_data)
        resource_resp = MagicMock()
        resource_resp.status_code = 200
        resource_resp.text = ""
        mock_get.side_effect = [app_resp, resource_resp]

        servers = self.pelican.get_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["status"], "unavailable")  # fallback

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_resource_http_fail(self, mock_get):
        # Resource call fails with 500
        mock_servers_data = {"data": [
            {"attributes": {"identifier": "x", "external_id": "ex", "uuid": "id", "name": "n", "description": "desc"}}]}
        app_resp = MagicMock()
        app_resp.text = json.dumps(mock_servers_data)
        res_resp = MagicMock()
        res_resp.status_code = 500
        res_resp.text = "fail"
        mock_get.side_effect = [app_resp, res_resp]

        servers = self.pelican.get_servers()
        self.assertEqual(servers[0]["status"], "unavailable")

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_exception_in_resources(self, mock_get):
        # Exception while fetching resource status
        mock_servers_data = {"data": [
            {"attributes": {"identifier": "x", "external_id": "ex", "uuid": "id", "name": "n", "description": "desc"}}]}
        app_resp = MagicMock()
        app_resp.text = json.dumps(mock_servers_data)
        mock_get.side_effect = [app_resp, Exception("Network error")]

        servers = self.pelican.get_servers()
        self.assertEqual(servers[0]["status"], "unavailable")  # fallback

    @patch("src.pelican_manager.requests.get")
    def test_get_servers_empty(self, mock_get):
        # No servers returned
        app_resp = MagicMock()
        app_resp.text = json.dumps({"data": []})
        mock_get.return_value = app_resp

        servers = self.pelican.get_servers()
        self.assertEqual(servers, [])


if __name__ == "__main__":
    unittest.main()
