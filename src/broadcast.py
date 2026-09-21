"""
broadcast.py
Broadcasts data to the websocket.
"""
import json
import queue
import threading
import weakref
from src import discord_client

# Global websocket reference
websock = []

# Send timeout (seconds) applied to each socket before a send is attempted.
# Bounds how long a single stalled target can hold up its own send queue.
SEND_TIMEOUT = 5

# Per-target send queue/thread bookkeeping. Keyed by the socket object
# itself (via a weak-key mapping) rather than id(), so a garbage-collected
# and later reused id cannot be mistaken for a live entry.
_sender_lock = threading.Lock()
_sender_queues = weakref.WeakKeyDictionary()
_sender_threads = weakref.WeakKeyDictionary()


def set_websocket(ws, name):
    """Set the global websocket instance."""
    global websock  # pylint: disable=global-variable-not-assigned
    websock.append({"socket": ws, 'name': name})

def unset_websocket(ws):
    """Remove the websocket instance from the global list."""
    global websock  # pylint: disable=global-variable-not-assigned
    websock[:] = [item for item in websock if item.get('socket') is not ws]
    _stop_send_queue(ws)


def _socket_sender_loop(mc_socket, send_queue):
    """Dedicated sender loop for one target socket.

    A single thread per target pulls queued payloads in FIFO order and
    sends them one at a time, so sends to the same target are delivered
    in the order they were broadcast. A short socket timeout bounds how
    long a stalled target can hold up its own queue: a timed-out send is
    caught and logged like any other send failure, and the loop moves on
    to the next queued payload instead of parking indefinitely.
    """
    while True:
        payload = send_queue.get()
        if payload is None:  # sentinel: stop the thread
            break
        try:
            if hasattr(mc_socket, 'sock') and mc_socket.sock:
                mc_socket.sock.settimeout(SEND_TIMEOUT)
            mc_socket.send(payload)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Failed to send message: {e}")


def _get_send_queue(mc_socket):
    """Get, creating on first use, the dedicated send queue for a socket.

    Creating the queue and its worker thread under a lock ensures at most
    one worker thread ever exists per target, however many broadcasts are
    in flight concurrently.
    """
    with _sender_lock:
        send_queue = _sender_queues.get(mc_socket)
        if send_queue is None:
            send_queue = queue.Queue()
            _sender_queues[mc_socket] = send_queue
            thread = threading.Thread(
                target=_socket_sender_loop,
                args=(mc_socket, send_queue),
                daemon=True,
            )
            _sender_threads[mc_socket] = thread
            thread.start()
        return send_queue


def _stop_send_queue(mc_socket):
    """Stop and forget the dedicated sender thread for a socket, if any."""
    with _sender_lock:
        send_queue = _sender_queues.pop(mc_socket, None)
        _sender_threads.pop(mc_socket, None)
    if send_queue is not None:
        send_queue.put(None)


def _send_to_minecraft_servers(origin, data, except_origin):
    """Queue the tellraw payload for every connected Minecraft server.

    Enqueuing is non-blocking, so callers on latency-sensitive threads
    (e.g. the Discord gateway event loop) are not held up by a slow or
    stalled Minecraft websocket. The actual blocking send happens on each
    target's own dedicated sender thread, in FIFO order.
    """
    for sock in websock:
        mc_socket = sock.get('socket')
        if hasattr(mc_socket, 'sock') and mc_socket.sock and mc_socket.sock.connected:
            if origin['external_id'] != sock.get('name') and except_origin:
                payload = json.dumps({"event": "send command", "args": [data]})
                _get_send_queue(mc_socket).put(payload)
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

        # Queueing to each target's dedicated sender is fast and
        # non-blocking, so this can run on the calling thread without
        # risking a stall on a slow Minecraft socket.
        _send_to_minecraft_servers(origin, data, except_origin)
