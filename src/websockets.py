""" Websockets"""

import threading
import json
import os
import time
import re
import requests
import websocket

from requests.exceptions import RequestException
from src.broadcast import set_websocket
from src.minecraft import parse_output
from src.debug import is_debug


class Websockets:
    """ Websockets class"""
    ws = ''
    server = []
    token = ''
    origin = ''
    error_count = 0

    def __init__(self, server):
        super().__init__()
        if is_debug():
            print("[src/websockets] Initialising Websockets")
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
                case 403:
                    raise PermissionError(
                        "403 Forbidden: Check your API key permissions and that the key is a "
                        "Client API key.")

            response.raise_for_status()

            data = response.json().get('data', {})
            self.token = data.get('token')
            return  # Success, exit the retry loop

        except ConnectionError:
            raise RequestException("Connection refused")

        except RequestException:
            raise RequestException("Connection error while fetching websocket credentials")

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
                        if is_debug():
                            print("Token expired, reconnecting...")
                        ws.close()
                        self.get_websocket_credentials(self.server['identifier'])
                        time.sleep(3)
                        self.connect_to_server(self.server)

                    case "auth required":
                        if is_debug():
                            print("Auth required - sending token...")
                        ws.send(json.dumps({"event": "auth", "args": self.token}))

                    case "auth success":
                        if is_debug():
                            print(f"Auth successful on {self.server['external_id']} "
                                  f"- starting keep-alive pings")
                        print("[INFO] Ready to receive messages.")

                        def keep_alive():
                            while True:
                                try:
                                    ws.send(json.dumps({"event": "send stats"}))
                                except ConnectionError as e:
                                    print(f"[ERROR] {e}")
                                    break
                                time.sleep(30)

                        threading.Thread(target=keep_alive, daemon=False).start()

                    case "console output":
                        raw_output = args[0]
                        # Strip ANSI escape sequences
                        cleaned_output = re.sub(r'(?:\x1b\[[0-9;]*m)*', '', raw_output)

                        print((None,
                               f"RAW: [{self.server['external_id']}] {cleaned_output}")[is_debug()])

                        if len(args) == 1:
                            parse_output(f"[{self.server['external_id']}] {cleaned_output}",
                                         server)
                    case _:
                        pass
            except json.JSONDecodeError:
                print(f"[{self.server['external_id']}] Failed to decode message")

        def on_error(ws, error):
            if is_debug():
                print("WebSocket error:", error)
            print("[WARN] Websocket error. Closing socket and retrying...")
            ws.close()
            self.connect_to_server(self.server)
            self.error_count += 1

            if self.error_count == 3:
                print("[WARN] Websocket error count exceeded. Waiting 5 minutes.")
                time.sleep(600)
                self.error_count = 0

            print("[INFO] Websocket error count reset. Retrying...")
            time.sleep(3)

        def on_close(ws, close_status_code, close_msg):  # pylint: disable=unused-argument
            if is_debug():
                print(f"WebSocket closed — Code: {close_status_code}, "
                      f"Reason: {close_msg}")
            print("[WARN] Websocket closed. Retrying...")
            self.connect_to_server(self.server)

        def on_open(ws):
            if is_debug():
                print("WebSocket connection established")
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
