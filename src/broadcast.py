import json

# Global websocket reference
websock = []


def set_websocket(ws, name):
    """Set the global websocket instance."""
    global websock
    websock.append({"socket": ws, 'name': name})


def broadcast_to_all(origin, data, except_origin=False):
    """Broadcast data to all servers except the origin."""
    if len(websock) > 0:
        for sock in websock:
            mc_socket = sock.get('socket')
            if hasattr(mc_socket, 'sock') and mc_socket.sock and mc_socket.sock.connected:
                try:
                    if origin['external_id'] != sock.get('name') and except_origin:
                        mc_socket.send(json.dumps({"event": "send command", "args": [data]}))
                    else:
                        print(f"Origin server: {origin}")
                except Exception as e:
                    print(f"[ERROR] Failed to send message: {e}")
            else:
                print("[WARN] WebSocket is not connected, cannot send message")
