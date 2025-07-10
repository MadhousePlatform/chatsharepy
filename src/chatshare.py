#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""

import os

from src.events import EventEmitter
from src.discord import DiscordClient

REQUIRED_ENV_VARS = [
    'PANEL_API_URL',
    'PANEL_APPLICATION_KEY',
    'PANEL_CLIENT_KEY',
    'DISCORD_TOKEN',
    'DISCORD_CHANNEL',
]

for var in REQUIRED_ENV_VARS:
    value = os.environ.get(var)
    if not value:  # catches None and empty string
        raise ValueError(f"Please set the {var} environment variable.")

def main():
    """
    Main entry point for the Chatshare application.
    """
    print("Welcome to Chatshare!")

    # Initialize the event emitter
    event_emitter = EventEmitter()

    # Initialize the Discord client
    client = DiscordClient(event_emitter)
    client.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
