"""
Event emitter class
"""
import asyncio
import inspect


class EventEmitter:
    """
    Event emitter class
    """

    def __init__(self):
        """
        Initialise the event emitter
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
            res = listener(*args, **kwargs)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    loop.create_task(res)
                else:
                    asyncio.run(res)
