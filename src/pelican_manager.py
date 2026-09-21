""" Pelican manager"""
import os
import json
import threading

import requests

from src.logger import logger

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
            'Authorization': f'Bearer {os.getenv("PANEL_APPLICATION_KEY")}',
            'Content-Type': 'application/json'
        }

        try:
            req = requests.get(
                f'{os.getenv("PANEL_API_URL")}/application/servers', headers=headers, timeout=10)

            data = json.loads(req.text).get('data', [])

        except requests.exceptions.ConnectionError as e:
            logger.error("Exception while fetching servers from the panel: %s", e, exc_info=True)
            return servers

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error(
                "Unexpected exception while fetching servers from the panel: %s",
                e, exc_info=True)
            return servers

        # Headers for client API
        client_headers = {
            'Authorization': f'Bearer {os.getenv("PANEL_CLIENT_KEY")}',
            'Content-Type': 'application/json'
        }

        for item in data:
            attributes = item.get('attributes', {})
            identifier = attributes.get('identifier')

            # Defaults in case of failure
            status = "unavailable"

            try:
                req2 = requests.get(
                    f'{os.getenv("PANEL_API_URL")}/client/servers/{identifier}/resources',
                    headers=client_headers,
                    timeout=10
                )

                if req2.status_code == 200 and req2.text.strip():
                    parsed = json.loads(req2.text)
                    attr = parsed.get('attributes', {})
                    status = attr.get('current_state', 'unknown')
                else:
                    logger.warning(
                        "Failed to fetch status for %s (HTTP %s)",
                        identifier, req2.status_code)


            except ConnectionError as e:
                logger.error("Exception while fetching status for %s: %s",
                             identifier, e, exc_info=True)

            except Exception as e: # pylint: disable=broad-exception-caught
                logger.error("Unexpected exception while fetching status for %s: %s",
                             identifier, e, exc_info=True)

            # Build the final server object
            if attributes.get('external_id'):
                servers.append({
                    "external_id": attributes.get("external_id"),
                    "uuid": attributes.get("uuid"),
                    "identifier": identifier,
                    "name": attributes.get("name"),
                    "description": attributes.get("description"),
                    "status": status,
                })

        return servers
