import websocket
import threading
import json
import os
import time
import requests


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

            data = json.loads(message)

            match event:
                case "stats":
                    pass  # Ignore stats

                case "jwt error":
                    print("⚠ Token expired, reconnecting...")
                    ws.close()
                    time.sleep(1)
                    connect_to_server(server['identifier'])

                case "auth required":
                    print("Auth required - sending token...")
                    ws.send(json.dumps({
                        "event": "auth",
                        "args": token
                    }))

                case "auth success":
                    print("Auth successful - starting keep-alive pings")

                    def keep_alive():
                        while True:
                            try:
                                ws.send(json.dumps({"event": "send stats"}))
                                print("Sent keep-alive ping")
                            except Exception as e:
                                print("Failed to send ping:", e)
                                break
                            time.sleep(30)

                    threading.Thread(target=keep_alive, daemon=False).start()

                case "status":
                    print(f"Server status: {args[0]}")

                case _:
                    print(f"Event: {event}, Args: {args}")

        except json.JSONDecodeError:
            print("Failed to decode message")

    def on_error(ws, error):
        print("WebSocket error:", error)

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket closed — Code: {close_status_code}, Reason: {close_msg}")

    def on_open(ws):
        print("WebSocket connection established")
        time.sleep(3)
        ws.send(json.dumps({
            "event": "auth",
            "args": [token]
        }))

    ws = websocket.WebSocketApp(
        f"{os.environ['PANEL_WSS_URL']}/servers/{server['uuid']}/ws?token={os.environ['WINGS_TOKEN']}",
        header={"Authorization": f"Bearer {os.environ['WINGS_TOKEN']}", "Origin": "https://peli.sketchni.uk/"},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Run WebSocket in a thread
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()
