""" Pelican manager"""
import os
import json
import threading

import requests

from src.debug import is_debug


class Pelican(threading.Thread):
    """ Pelican manager class"""

    @staticmethod
    def get_servers() -> list:
        """
        Get all containers and their current statuses.
        """
        servers = []

        # Headers for application API
        headers = {
            'Authorization': f'Bearer {os.environ["PANEL_APPLICATION_KEY"]}',
            'Content-Type': 'application/json'
        }

        req = requests.get(
            f'{os.environ["PANEL_API_URL"]}/application/servers', headers=headers, timeout=10)
        if is_debug():
            print("Making GET request to application::servers endpoint.")

        data = json.loads(req.text).get('data', [])

        # Headers for client API
        client_headers = {
            'Authorization': f'Bearer {os.environ["PANEL_CLIENT_KEY"]}',
            'Content-Type': 'application/json'
        }

        for item in data:
            attributes = item.get('attributes', {})
            identifier = attributes.get('identifier')

            # Defaults in case of failure
            status = "unavailable"

            try:
                req2 = requests.get(
                    f'{os.environ["PANEL_API_URL"]}/client/servers/{identifier}/resources',
                    headers=client_headers,
                    timeout=10
                )
                if is_debug():
                    print("Making GET request to client::server::resources endpoint.")

                if req2.status_code == 200 and req2.text.strip():
                    parsed = json.loads(req2.text)
                    attr = parsed.get('attributes', {})
                    status = attr.get('current_state', 'unknown')
                else:
                    print(f"[WARN] Failed to fetch status for {identifier} "
                          f"(HTTP {req2.status_code})")


            except ConnectionError as e:
                print(f"[ERROR] Exception while fetching status for {identifier}: {e}")

            except Exception as e:
                print(f"[ERROR] Unexpected exception while fetching status for {identifier}: {e}")

            # Build the final server object
            servers.append({
                "external_id": attributes.get("external_id"),
                "uuid": attributes.get("uuid"),
                "identifier": identifier,
                "name": attributes.get("name"),
                "description": attributes.get("description"),
                "status": status,
            })

        return servers
