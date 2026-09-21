"""
broadcast.py
Broadcasts data to the websocket.
"""
import json
import threading
from src import discord_client

# Global websocket reference
websock = []


def set_websocket(ws, name):
    """Set the global websocket instance."""
    global websock  # pylint: disable=global-variable-not-assigned
    websock.append({"socket": ws, 'name': name})

def unset_websocket(ws):
    """Remove the websocket instance from the global list."""
    global websock  # pylint: disable=global-variable-not-assigned
    websock[:] = [item for item in websock if item.get('socket') is not ws]


def _send_to_minecraft_servers(origin, data, except_origin):
    """Send the tellraw payload to every connected Minecraft server.

    Runs the blocking per-socket sends so callers on latency-sensitive
    threads (e.g. the Discord gateway event loop) are not held up by a
    slow or stalled Minecraft websocket.
    """
    for sock in websock:
        mc_socket = sock.get('socket')
        if hasattr(mc_socket, 'sock') and mc_socket.sock and mc_socket.sock.connected:
            try:
                if origin['external_id'] != sock.get('name') and except_origin:
                    mc_socket.send(json.dumps({"event": "send command", "args": [data]}))
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"[ERROR] Failed to send message: {e}")
        else:
            print("[WARN] WebSocket is not connected, cannot send message")


def broadcast_to_all(origin, data, message, except_origin=False, relay_to_discord=True):
    """Broadcast data to all servers except the origin.

    Args:
        origin: dict describing the message's origin server.
        data: tellraw payload to send to connected Minecraft servers.
        message: human-readable text to relay to Discord.
        except_origin: only send to sockets other than the origin's when True.
        relay_to_discord: whether to also relay this message to Discord. This
            must be False for messages that originated in Discord, so the bot
            does not echo a Discord user's own message back into the same
            channel.
    """
    if len(websock) > 0:
        if relay_to_discord:
            discord_client.discord_c.send_message(message)

        # The websocket sends are blocking I/O; do them off the calling
        # thread so a slow Minecraft socket can't stall a caller such as
        # the Discord gateway event loop.
        threading.Thread(
            target=_send_to_minecraft_servers,
            args=(origin, data, except_origin),
            daemon=True,
        ).start()
