import websocket
import threading
import json
import os
import time
import requests
import re

from src.broadcast import set_global_websocket
from src.minecraft import parse_output
from src.debug import DEBUG_MODE


def get_websocket_credentials(server_id):
    headers = {
        'Authorization': f'Bearer {os.environ["PANEL_CLIENT_KEY"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    url = f"{os.environ['PANEL_API_URL']}/client/servers/{server_id}/websocket"
    response = requests.get(url, headers=headers)

    if response.status_code == 403:
        raise PermissionError("403 Forbidden: Check your API key permissions and that the key is a Client API key.")

    response.raise_for_status()

    data = response.json().get('data', {})
    return data.get('token')


def connect_to_server(server):
    token = get_websocket_credentials(server['identifier'])

    def on_message(ws, message):
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
                    time.sleep(1)
                    connect_to_server(server)

                case "auth required":
                    if DEBUG_MODE:
                        print("Auth required - sending token...")
                    ws.send(json.dumps({"event": "auth", "args": token}))

                case "auth success":
                    if DEBUG_MODE:
                        print(f"Auth successful on {server['identifier']} - starting keep-alive pings")
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

                    if DEBUG_MODE:
                        print(f"RAW: [{server['external_id']}] {cleaned_output}")

                    if len(args) == 1:
                        parse_output(f"[{server['external_id']}] {cleaned_output}", server)
        except json.JSONDecodeError:
            print(f"[{server['identifier']}] Failed to decode message")

    def on_error(ws, error):
        if DEBUG_MODE:
            print("WebSocket error:", error)

    def on_close(ws, close_status_code, close_msg):
        if DEBUG_MODE:
            print(f"WebSocket closed — Code: {close_status_code}, Reason: {close_msg}")

    def on_open(ws):
        if DEBUG_MODE:
            print("WebSocket connection established")
        time.sleep(3)
        ws.send(json.dumps({"event": "auth", "args": [token]}))

    ws = websocket.WebSocketApp(
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

    set_global_websocket(ws)

    # Run WebSocket in a thread
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()
