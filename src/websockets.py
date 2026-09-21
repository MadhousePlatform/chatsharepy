""" Websockets"""

import threading
import json
import os
import time
import re
import requests
import websocket

from requests.exceptions import RequestException
from src.broadcast import set_websocket, unset_websocket
from src.minecraft import parse_output
from src.logger import logger


class Websockets:
    """ Websockets class"""
    ws = ''
    server = []
    token = ''
    origin = ''
    error_count = 0

    def __init__(self, server):
        super().__init__()
        logger.debug("[src/websockets] Initialising Websockets")
        self.origin = server['external_id']
        self.error_count = 0

    def get_websocket_credentials(self, server_id) -> None:
        """ Get websocket credentials from the panel """
        headers = {
            'Authorization': f'Bearer {os.getenv("PANEL_CLIENT_KEY")}',
            'Content-Type': 'application/json'
        }

        url = f"{os.getenv('PANEL_API_URL')}/client/servers/{server_id}/websocket"

        try:
            response = requests.get(url, headers=headers, timeout=30)

            match response.status_code:
                case 401:
                    raise PermissionError(
                        "401 Unauthorized: Check your API key permissions.")
                case 403:
                    raise PermissionError(
                        "403 Forbidden: Check your API key permissions and that the key is a "
                        "Client API key.")

            response.raise_for_status()

            data = response.json().get('data', {})
            self.token = data.get('token')
            return  # Success, exit the retry loop

        except RequestException:
            raise RequestException("Connection error while fetching websocket credentials") # pylint: disable=raise-missing-from

    def connect_to_server(self, server) -> None:  # pylint: disable=too-many-statements
        """ Connect to server """
        self.server = server
        self.get_websocket_credentials(self.server['identifier'])

        def on_message(ws, message: str):
            try:
                msg = json.loads(message)
                event = msg.get("event")
                args = msg.get("args", [])

                match event:
                    case "jwt error":
                        logger.debug("Token expired, reconnecting...")
                        ws.close()

                    case "auth required":
                        logger.debug("Auth required - sending token...")
                        ws.send(json.dumps({"event": "auth", "args": [self.token]}))

                    case "auth success":
                        logger.debug(
                            "Auth successful on %s - starting keep-alive pings",
                            self.server['external_id'])
                        logger.info("Ready to receive messages.")

                        def keep_alive():
                            while True:
                                try:
                                    ws.send(json.dumps({"event": "send stats"}))
                                except ConnectionError as e:
                                    logger.error("%s", e, exc_info=True)
                                    break
                                time.sleep(30)

                        threading.Thread(target=keep_alive, daemon=True).start()

                    case "console output":
                        if len(args) == 1:
                            raw_output = args[0]
                            # Strip ANSI escape sequences
                            cleaned_output = re.sub(r'(?:\x1b\[[0-9;]*m)*', '', raw_output)

                            logger.debug(
                                "RAW: [%s] %s", self.server['external_id'], cleaned_output)

                            parse_output(f"[{self.server['external_id']}] {cleaned_output}",
                                         server)
                    case _:
                        pass
            except json.JSONDecodeError:
                logger.error(
                    "[%s] Failed to decode message", self.server['external_id'], exc_info=True)

        def on_error(ws, error):
            logger.debug("WebSocket error: %s", error)
            logger.warning("Websocket error. Closing socket and retrying...")
            ws.close()

        def on_close(ws, close_status_code, close_msg):  # pylint: disable=unused-argument
            logger.debug(
                "WebSocket closed — Code: %s, Reason: %s", close_status_code, close_msg)
            unset_websocket(self.ws)
            logger.warning("Websocket closed. Retrying...")
            self.connect_to_server(self.server)

        def on_open(ws):
            logger.debug("WebSocket connection established")
            time.sleep(3)
            ws.send(json.dumps({"event": "auth", "args": [self.token]}))

        panel_url = os.getenv('PANEL_WSS_URL')
        wings_token = os.getenv('WINGS_TOKEN')
        self.ws = websocket.WebSocketApp(
            f"{panel_url}/servers/{server['uuid']}/ws?token={wings_token}",
            header=[
                f"Authorization: Bearer {wings_token}",
                f"Origin: {os.getenv('PANEL_ORIGIN_URL')}",
            ],
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        set_websocket(self.ws, server['external_id'])
        self.server = server

        # Run WebSocket in a thread
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
