"""
Event emitter class
"""

from src.log import logger

class EventEmitter:
    """
    Event emitter class
    """

    def __init__(self):
        """
        Initialize the event emitter
        """
        logger.debug("Initializing event emitter")
        self.events = {}

    def on(self, event, listener):
        """
        Add a listener to an event

        Args:
            event: Event name
            listener: Listener function
        """
        if event not in self.events:
            logger.debug(f"Registering event {event}")
            self.events[event] = []

        logger.debug(f"Registering listener {listener} for event {event}")
        self.events[event].append(listener)

    def off(self, event, listener):
        """
        Remove a listener from an event

        Args:
            event: Event name
            listener: Listener function
        """
        if event in self.events:
            try:
                logger.debug(f"Removing listener {listener} for event {event}")
                self.events[event].remove(listener)
            except ValueError:
                logger.error(f"Listener {listener} not found for event {event}")
                pass

    def emit(self, event, *args, **kwargs):
        """
        Emit an event

        Args:
            event: Event name
            args: Arguments
            kwargs: Keyword arguments
        """
        listeners = self.events.get(event, [])
        for listener in listeners:
            logger.debug(f"Emitting event {event} to listener {listener}")
            listener(*args, **kwargs)
