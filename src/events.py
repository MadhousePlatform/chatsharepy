"""
Event emitter class
"""

class EventEmitter:
    """
    Event emitter class
    """

    def __init__(self):
        """
        Initialize the event emitter
        """
        self.events = {}

    def on(self, event, listener):
        """
        Add a listener to an event

        Args:
            event: Event name
            listener: Listener function
        """
        if event not in self.events:
            self.events[event] = []
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
                self.events[event].remove(listener)
            except ValueError:
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
            listener(*args, **kwargs)
