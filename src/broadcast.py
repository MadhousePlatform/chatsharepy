"""
broadcast.py
Broadcasts data to the websocket.
"""
import json
import queue
import threading
import weakref
from src import discord_client
from src.logger import logger

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

# Sockets whose teardown has started. Checked by _get_send_queue under the
# same lock as the pop in _stop_send_queue, so a socket that is closing can
# never have a second, untracked worker thread created for it: once torn
# down, it stays torn down rather than being recreated by a racing enqueue.
_closing_sockets = weakref.WeakSet()


def set_websocket(ws, name):
    """Set the global websocket instance."""
    global websock  # pylint: disable=global-variable-not-assigned
    with _sender_lock:
        websock.append({"socket": ws, 'name': name})

def unset_websocket(ws):
    """Remove the websocket instance from the global list."""
    global websock  # pylint: disable=global-variable-not-assigned
    with _sender_lock:
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
            logger.error("Failed to send message: %s", e, exc_info=True)


def _get_send_queue(mc_socket):
    """Get, creating on first use, the dedicated send queue for a socket.

    Creating the queue and its worker thread under a lock ensures at most
    one worker thread ever exists per target, however many broadcasts are
    in flight concurrently. A socket whose teardown has started (see
    _stop_send_queue) is never handed a fresh queue/thread here: doing so
    would create a second, untracked worker thread that could never be
    signalled to stop, since teardown for that socket has already run and
    will not run again. Returns None for a closing socket, so the caller
    can drop the enqueue instead.
    """
    with _sender_lock:
        if mc_socket in _closing_sockets:
            return None
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
    """Stop and forget the dedicated sender thread for a socket, if any.

    The socket is marked as closing under the same lock that guards
    queue/thread creation in _get_send_queue, atomically with the pop from
    the tracking dicts. This closes the window where a concurrent enqueue
    could otherwise observe the socket as unregistered and create a second,
    orphaned queue and worker thread for it that would never receive a stop
    signal: once a socket starts closing, _get_send_queue will refuse to
    recreate it, however the two calls interleave.
    """
    with _sender_lock:
        _closing_sockets.add(mc_socket)
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

    A snapshot of websock is taken under _sender_lock before iterating, so
    a concurrent unset_websocket mutating the list in place (which also
    takes the lock) cannot shrink the list out from under this loop and
    cause the plain list iterator to silently skip an entry: every socket
    present when the broadcast started either gets a genuine send attempt
    here or was already excluded from the snapshot.
    """
    with _sender_lock:
        targets = list(websock)
    for sock in targets:
        mc_socket = sock.get('socket')
        if hasattr(mc_socket, 'sock') and mc_socket.sock and mc_socket.sock.connected:
            if origin['external_id'] != sock.get('name') and except_origin:
                payload = json.dumps({"event": "send command", "args": [data]})
                send_queue = _get_send_queue(mc_socket)
                if send_queue is not None:
                    send_queue.put(payload)
                else:
                    logger.warning("Socket is closing, dropping queued message")
        else:
            logger.warning("WebSocket is not connected, cannot send message")


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
    with _sender_lock:
        has_targets = len(websock) > 0
    if has_targets:
        if relay_to_discord:
            discord_client.discord_c.send_message(message)

        # Queueing to each target's dedicated sender is fast and
        # non-blocking, so this can run on the calling thread without
        # risking a stall on a slow Minecraft socket.
        _send_to_minecraft_servers(origin, data, except_origin)
