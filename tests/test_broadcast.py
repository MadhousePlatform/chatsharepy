"""
Tests for src/broadcast.py
"""
import threading
import time
import unittest
from unittest.mock import Mock, patch

from src import broadcast
from src.broadcast import broadcast_to_all, set_websocket, unset_websocket


def _wait_until(predicate, timeout=2.0, interval=0.01):
    """Poll predicate() until it is truthy or the timeout elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


class TestBroadcastToAll(unittest.TestCase):
    """Tests for broadcast_to_all."""

    def setUp(self):
        """Ensure the module-level websocket list starts empty for each test."""
        broadcast.websock = []

    def tearDown(self):
        """Leave the module-level websocket list clean for other test modules."""
        broadcast.websock = []

    def _add_connected_socket(self, name):
        mock_socket = Mock()
        mock_socket.sock.connected = True
        set_websocket(mock_socket, name)
        return mock_socket

    @patch('src.broadcast.discord_client')
    def test_relays_to_discord_by_default(self, mock_discord_client):
        """A Minecraft-sourced message should still reach Discord."""
        self._add_connected_socket('vanilla')

        broadcast_to_all({'external_id': 'other'}, 'data', 'message', except_origin=True)

        mock_discord_client.discord_c.send_message.assert_called_once_with('message')

    @patch('src.broadcast.discord_client')
    def test_does_not_relay_to_discord_when_message_originated_there(self, mock_discord_client):
        """
        A Discord-originated message must not be echoed straight back to
        Discord by the bot.
        """
        self._add_connected_socket('vanilla')

        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )

        mock_discord_client.discord_c.send_message.assert_not_called()

    @patch('src.broadcast.discord_client')
    def test_still_sends_to_minecraft_sockets_when_discord_relay_skipped(self, mock_discord_client):
        """Skipping the Discord relay must not stop the message reaching Minecraft."""
        mock_socket = self._add_connected_socket('vanilla')

        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )

        # The Minecraft send happens on a background thread; give it a
        # moment to run.
        for _ in range(50):
            if mock_socket.send.called:
                break
            time.sleep(0.01)

        mock_discord_client.discord_c.send_message.assert_not_called()
        mock_socket.send.assert_called_once()

    @patch('src.broadcast.discord_client')
    def test_minecraft_send_does_not_block_caller(self, mock_discord_client):
        """
        The socket send loop must run off the calling thread so a slow
        Minecraft socket cannot stall the caller (e.g. the Discord gateway
        event loop).
        """
        mock_socket = self._add_connected_socket('vanilla')
        release_event = threading.Event()

        def slow_send(_payload):
            # Block until released, simulating a stalled Minecraft socket.
            release_event.wait(timeout=2)

        mock_socket.send.side_effect = slow_send

        started = time.monotonic()
        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )
        elapsed = time.monotonic() - started

        release_event.set()
        self.assertLess(elapsed, 0.5)
        _ = mock_discord_client

    @patch('src.broadcast.discord_client')
    def test_broadcasts_to_same_target_are_delivered_in_order(self, mock_discord_client):
        """
        Rapid broadcasts to the same target socket must be delivered in the
        order they were called, even though the actual send happens on a
        background thread.
        """
        mock_socket = self._add_connected_socket('vanilla')
        delivered = []
        send_started = threading.Event()

        def record_send(payload):
            # Give a second, concurrently-queued send a chance to race in
            # if ordering were not preserved.
            send_started.set()
            delivered.append(payload)

        mock_socket.send.side_effect = record_send

        broadcast_to_all(
            {'external_id': 'discord'}, 'first', 'first message',
            except_origin=True, relay_to_discord=False,
        )
        broadcast_to_all(
            {'external_id': 'discord'}, 'second', 'second message',
            except_origin=True, relay_to_discord=False,
        )

        self.assertTrue(_wait_until(lambda: len(delivered) == 2))
        self.assertIn('first', delivered[0])
        self.assertIn('second', delivered[1])
        _ = mock_discord_client

    @patch('src.broadcast.discord_client')
    def test_stalled_target_does_not_block_caller_or_other_targets(self, mock_discord_client):
        """
        A slow/stalled socket send must not block the calling thread, and
        must not prevent a broadcast to an independent target from
        completing.
        """
        stalled_socket = self._add_connected_socket('stalled')
        fast_socket = self._add_connected_socket('fast')
        release_event = threading.Event()

        def slow_send(_payload):
            release_event.wait(timeout=2)

        stalled_socket.send.side_effect = slow_send

        started = time.monotonic()
        broadcast_to_all(
            {'external_id': 'discord'}, 'data', 'message',
            except_origin=True, relay_to_discord=False,
        )
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.5)
        self.assertTrue(_wait_until(lambda: fast_socket.send.called))

        release_event.set()

    @patch('src.broadcast.discord_client')
    def test_send_failure_does_not_stop_later_sends_to_same_target(self, mock_discord_client):
        """
        A send that raises (e.g. a timed-out socket) must be caught and
        logged like any other send failure, and must not stop later
        broadcasts to the same target from being delivered.
        """
        mock_socket = self._add_connected_socket('vanilla')
        mock_socket.send.side_effect = [TimeoutError('send timed out'), None]

        broadcast_to_all(
            {'external_id': 'discord'}, 'first', 'first message',
            except_origin=True, relay_to_discord=False,
        )
        broadcast_to_all(
            {'external_id': 'discord'}, 'second', 'second message',
            except_origin=True, relay_to_discord=False,
        )

        self.assertTrue(_wait_until(lambda: mock_socket.send.call_count == 2))
        _ = mock_discord_client

    def test_unset_websocket_removes_entry(self):
        mock_socket = self._add_connected_socket('vanilla')
        unset_websocket(mock_socket)
        self.assertEqual(broadcast.websock, [])

    @patch('src.broadcast.discord_client')
    def test_concurrent_unset_during_broadcast_does_not_skip_a_socket(self, mock_discord_client):
        """
        A concurrent unset_websocket that mutates the websock list while a
        broadcast is partway through iterating it must not cause the
        broadcast to silently skip a socket that was still present when the
        broadcast started.

        This forces the exact interleaving the race depends on: the
        broadcast is paused (via a patched _get_send_queue) right after it
        starts handling the *second* socket in the list, and a second
        thread then removes the *first* socket from websock while the
        broadcast is paused there. Removing an earlier entry shifts every
        later entry's index down by one. With a plain, unlocked
        `for sock in websock:` iteration, CPython's list iterator tracks
        only a numeric index into the live list object, so after this
        shift its next index runs off the end of the shrunk list one
        socket early: the last socket (socket_c), never removed and still
        connected, is silently skipped even though it was present for the
        whole broadcast. A stable snapshot taken under the lock before
        iteration begins is unaffected by the later removal, so socket_c
        is still reached.
        """
        socket_a = self._add_connected_socket('a')
        socket_b = self._add_connected_socket('b')
        socket_c = self._add_connected_socket('c')

        entered_second_socket = threading.Event()
        resume_broadcast = threading.Event()
        real_get_send_queue = broadcast._get_send_queue  # pylint: disable=protected-access

        def paced_get_send_queue(mc_socket):
            if mc_socket is socket_b:
                entered_second_socket.set()
                resume_broadcast.wait(timeout=2)
            return real_get_send_queue(mc_socket)

        with patch.object(broadcast, '_get_send_queue', side_effect=paced_get_send_queue):
            broadcast_thread = threading.Thread(
                target=broadcast._send_to_minecraft_servers,  # pylint: disable=protected-access
                args=({'external_id': 'discord'}, 'data', True),
            )
            broadcast_thread.start()

            self.assertTrue(entered_second_socket.wait(timeout=2))
            # Remove socket_a, the entry before socket_b, while the
            # broadcast is paused mid-iteration on socket_b. This shifts
            # socket_c's index down by one in the live list.
            unset_websocket(socket_a)
            resume_broadcast.set()
            broadcast_thread.join(timeout=2)

        # socket_a's send was already queued before it was unset, so it
        # legitimately gets a genuine send attempt too; the point of this
        # test is socket_c, which must not be silently skipped.
        self.assertTrue(_wait_until(lambda: socket_a.send.called))
        self.assertTrue(_wait_until(lambda: socket_b.send.called))
        # socket_c was still connected and present in websock for the
        # whole broadcast; a concurrent unset of an earlier socket must
        # not cause it to be silently skipped by a mid-iteration list
        # mutation.
        self.assertTrue(_wait_until(lambda: socket_c.send.called))
        _ = mock_discord_client

    def test_teardown_racing_enqueue_does_not_orphan_a_second_thread(self):
        """
        A concurrent enqueue that races _stop_send_queue's teardown of a
        socket must not create a second, untracked worker thread for that
        socket.

        This forces the exact interleaving the race depends on, rather than
        relying on timing: _get_send_queue is called from a second thread
        that is held just before it acquires _sender_lock, released only
        after _stop_send_queue has done its work, so the racing call always
        lands in the window right after teardown.
        """
        mock_socket = self._add_connected_socket('vanilla')

        # Register the socket's queue/thread up front, as a live broadcast
        # would have done before teardown starts.
        original_queue = broadcast._get_send_queue(mock_socket)  # pylint: disable=protected-access
        original_thread = broadcast._sender_threads[mock_socket]  # pylint: disable=protected-access
        self.assertTrue(original_thread.is_alive())

        teardown_done = threading.Event()
        racing_queue_holder = {}

        def racing_enqueue():
            # Wait for _stop_send_queue to finish before calling
            # _get_send_queue, landing squarely in the post-teardown window
            # the race depends on.
            teardown_done.wait(timeout=2)
            racing_queue_holder['queue'] = broadcast._get_send_queue(mock_socket)  # pylint: disable=protected-access

        racer = threading.Thread(target=racing_enqueue)
        racer.start()

        broadcast._stop_send_queue(mock_socket)  # pylint: disable=protected-access
        teardown_done.set()
        racer.join(timeout=2)

        self.assertTrue(_wait_until(lambda: not original_thread.is_alive()))

        # The racing call must not have been handed a fresh queue/thread:
        # the socket is closing, so the enqueue is dropped rather than
        # spawning a second, unstoppable worker.
        self.assertIsNone(racing_queue_holder.get('queue'))
        self.assertNotIn(mock_socket, broadcast._sender_threads)  # pylint: disable=protected-access
        self.assertNotIn(mock_socket, broadcast._sender_queues)  # pylint: disable=protected-access

        # A subsequent broadcast to the now-closed socket must not spawn
        # another leaked, un-stoppable thread either.
        broadcast._send_to_minecraft_servers({'external_id': 'discord'}, 'data', True)  # pylint: disable=protected-access
        self.assertNotIn(mock_socket, broadcast._sender_threads)  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
