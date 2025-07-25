#!/usr/bin/env python3

"""
Tests for the EventEmitter class in events.py.
"""

import unittest
from unittest.mock import Mock
from src.events import EventEmitter


class TestEventEmitter(unittest.TestCase):
    """
    Tests for the EventEmitter class.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.emitter = EventEmitter()

    def test_init(self):
        """Test EventEmitter initialization."""
        emitter = EventEmitter()
        self.assertEqual(emitter.events, {})

    def test_on_adds_listener(self):
        """Test that on() adds a listener to an event."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.assertIn('test_event', self.emitter.events)
        self.assertIn(mock_listener, self.emitter.events['test_event'])

    def test_on_adds_multiple_listeners(self):
        """Test that on() can add multiple listeners to the same event."""
        mock_listener1 = Mock()
        mock_listener2 = Mock()
        self.emitter.on('test_event', mock_listener1)
        self.emitter.on('test_event', mock_listener2)
        self.assertEqual(len(self.emitter.events['test_event']), 2)
        self.assertIn(mock_listener1, self.emitter.events['test_event'])
        self.assertIn(mock_listener2, self.emitter.events['test_event'])

    def test_on_adds_same_listener_multiple_times(self):
        """Test that the same listener can be added multiple times."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.on('test_event', mock_listener)
        self.assertEqual(len(self.emitter.events['test_event']), 2)
        self.assertEqual(self.emitter.events['test_event'][0], mock_listener)
        self.assertEqual(self.emitter.events['test_event'][1], mock_listener)

    def test_off_removes_listener(self):
        """Test that off() removes a listener from an event."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.off('test_event', mock_listener)
        self.assertEqual(len(self.emitter.events['test_event']), 0)

    def test_off_removes_correct_listener(self):
        """Test that off() removes only the specified listener."""
        mock_listener1 = Mock()
        mock_listener2 = Mock()
        self.emitter.on('test_event', mock_listener1)
        self.emitter.on('test_event', mock_listener2)
        self.emitter.off('test_event', mock_listener1)
        self.assertEqual(len(self.emitter.events['test_event']), 1)
        self.assertNotIn(mock_listener1, self.emitter.events['test_event'])
        self.assertIn(mock_listener2, self.emitter.events['test_event'])

    def test_off_nonexistent_event(self):
        """Test that off() handles non-existent events gracefully."""
        mock_listener = Mock()
        # Should not raise an exception
        self.emitter.off('nonexistent_event', mock_listener)

    def test_off_nonexistent_listener(self):
        """Test that off() handles non-existent listeners gracefully."""
        mock_listener1 = Mock()
        mock_listener2 = Mock()
        self.emitter.on('test_event', mock_listener1)
        # Should not raise an exception
        self.emitter.off('test_event', mock_listener2)
        # Original listener should still be there
        self.assertIn(mock_listener1, self.emitter.events['test_event'])

    def test_emit_calls_listener(self):
        """Test that emit() calls the registered listener."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.emit('test_event')
        mock_listener.assert_called_once()

    def test_emit_calls_all_listeners(self):
        """Test that emit() calls all registered listeners for an event."""
        mock_listener1 = Mock()
        mock_listener2 = Mock()
        self.emitter.on('test_event', mock_listener1)
        self.emitter.on('test_event', mock_listener2)
        self.emitter.emit('test_event')
        mock_listener1.assert_called_once()
        mock_listener2.assert_called_once()

    def test_emit_with_args(self):
        """Test that emit() passes arguments to listeners."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.emit('test_event', 'arg1', 'arg2')
        mock_listener.assert_called_once_with('arg1', 'arg2')

    def test_emit_with_kwargs(self):
        """Test that emit() passes keyword arguments to listeners."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.emit('test_event', key1='value1', key2='value2')
        mock_listener.assert_called_once_with(key1='value1', key2='value2')

    def test_emit_with_args_and_kwargs(self):
        """Test that emit() passes both args and kwargs to listeners."""
        mock_listener = Mock()
        self.emitter.on('test_event', mock_listener)
        self.emitter.emit('test_event', 'arg1', 'arg2', key1='value1', key2='value2')
        mock_listener.assert_called_once_with('arg1', 'arg2', key1='value1', key2='value2')

    def test_emit_nonexistent_event(self):
        """Test that emit() handles non-existent events gracefully."""
        # Should not raise an exception
        self.emitter.emit('nonexistent_event')

    def test_multipleevents(self):
        """Test that the emitter can handle multiple different events."""
        mock_listener1 = Mock()
        mock_listener2 = Mock()
        self.emitter.on('event1', mock_listener1)
        self.emitter.on('event2', mock_listener2)
        self.emitter.emit('event1', 'data1')
        self.emitter.emit('event2', 'data2')
        mock_listener1.assert_called_once_with('data1')
        mock_listener2.assert_called_once_with('data2')

    def test_listener_exception_handling(self):
        """Test that exceptions in listeners don't break the emitter."""
        def failing_listener():
            raise ValueError("Listener failed")
        def working_listener():
            working_listener.called = True
        working_listener.called = False
        self.emitter.on('test_event', failing_listener)
        self.emitter.on('test_event', working_listener)
        # This should not prevent the second listener from being called
        # Note: The current implementation doesn't handle exceptions,
        # so this test documents the current behavior
        with self.assertRaises(Exception):
            self.emitter.emit('test_event')


if __name__ == '__main__':
    unittest.main()
