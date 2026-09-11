"""
broadcast.py
Broadcasts data to the websocket.
"""
import asyncio
import json
from src import discord_client

# Global websocket reference
websock = []


def set_websocket(ws, name):
    """Set the global websocket instance."""
    global websock  # pylint: disable=global-variable-not-assigned
    websock.append({"socket": ws, 'name': name})


def broadcast_to_all(origin, data, message, except_origin=False):
    """Broadcast data to all servers except the origin."""
    print(data)
    if len(websock) > 0:
        discord_client.discord_c.send_message(message),
        for sock in websock:
            mc_socket = sock.get('socket')
            if hasattr(mc_socket, 'sock') and mc_socket.sock and mc_socket.sock.connected:
                try:
                    if origin['external_id'] != sock.get('name') and except_origin:
                        mc_socket.send(json.dumps({"event": "send command", "args": [data]}))
                    else:
                        print(f"Origin server: {origin}")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"[ERROR] Failed to send message: {e}")
            else:
                print("[WARN] WebSocket is not connected, cannot send message")
