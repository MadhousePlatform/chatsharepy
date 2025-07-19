import websocket
import threading
import json
import os
import time
import requests
import re

from src.broadcast import set_websocket
from src.minecraft import parse_output
from src.debug import DEBUG_MODE

import time
import requests
from requests.exceptions import ConnectionError, RequestException


class Websockets(threading.Thread):
    ws = ''
    server = []
    token = ''
    origin = ''

    def __init__(self, server):
        super().__init__()
        if DEBUG_MODE:
            print("[src/websockets] Initialising Websockets")
        self.origin = server['external_id']

    def get_websocket_credentials(self, server_id, max_retries=3, backoff_factor=1) -> None:
        headers = {
            'Authorization': f'Bearer {os.environ["PANEL_CLIENT_KEY"]}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        url = f"{os.environ['PANEL_API_URL']}/client/servers/{server_id}/websocket"

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code == 403:
                    raise PermissionError(
                        "403 Forbidden: Check your API key permissions and that the key is a Client API key.")

                response.raise_for_status()

                data = response.json().get('data', {})
                self.token = data.get('token')
                return  # Success, exit the retry loop

            except ConnectionError as e:
                if "Name or service not known" in str(e) or "Failed to resolve" in str(e):
                    raise ConnectionError(
                        f"DNS resolution failed for {url}. Please check the hostname in PANEL_API_URL environment variable.") from e

                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    print(
                        f"Connection failed, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise ConnectionError(f"Failed to connect after {max_retries} attempts: {str(e)}") from e

            except RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    print(f"Request failed, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise RequestException(f"Request failed after {max_retries} attempts: {str(e)}") from e

    def connect_to_server(self, server) -> None:
        self.server = server
        self.get_websocket_credentials(self.server['identifier'])

        def on_message(ws, message: str):
            try:
                msg = json.loads(message)
                event = msg.get("event")
                args = msg.get("args", [])

                match event:
                    case "stats" | "status":
                        pass  # Ignore stats

                    case "jwt error":
                        if DEBUG_MODE:
                            print("Token expired, reconnecting...")
                        ws.close()
                        self.get_websocket_credentials(self.server['identifier'])
                        time.sleep(3)
                        self.connect_to_server(self.server)

                    case "auth required":
                        if DEBUG_MODE:
                            print("Auth required - sending token...")
                        ws.send(json.dumps({"event": "auth", "args": self.token}))

                    case "auth success":
                        if DEBUG_MODE:
                            print(f"Auth successful on {self.server['identifier']} - starting keep-alive pings")
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

                        print((None, f"RAW: [{self.server['external_id']}] {cleaned_output}")[DEBUG_MODE])

                        if len(args) == 1:
                            parse_output(f"[{self.server['external_id']}] {cleaned_output}", server)
            except json.JSONDecodeError:
                print(f"[{self.server['identifier']}] Failed to decode message")

        def on_error(ws, error):
            count = 0

            if DEBUG_MODE:
                print("WebSocket error:", error)
            print(f"[WARN] Websocket error. Closing socket and retrying...")
            ws.close()
            self.connect_to_server(self.server)
            count += 1

            if count == 3:
                print("[WARN] Websocket error count exceeded. Waiting 5 minutes.")
                time.sleep(600)
                count = 0

            print("[INFO] Websocket error count reset. Retrying...")
            time.sleep(3)

        def on_close(ws, close_status_code, close_msg):
            if DEBUG_MODE:
                print(f"WebSocket closed — Code: {close_status_code}, Reason: {close_msg}")
            print(f"[WARN] Websocket closed. Retrying...")
            self.connect_to_server(self.server)

        def on_open(ws):
            if DEBUG_MODE:
                print("WebSocket connection established")
            time.sleep(3)
            ws.send(json.dumps({"event": "auth", "args": [self.token]}))

        self.ws = websocket.WebSocketApp(
            f"{os.environ['PANEL_WSS_URL']}/servers/{server['uuid']}/ws?token={os.environ['WINGS_TOKEN']}",
            header=[
                f"Authorization: Bearer {os.environ['WINGS_TOKEN']}",
                "Origin: https://peli.sketchni.uk/"
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
