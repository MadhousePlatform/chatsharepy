#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""
import os
import time

from src.debug import DEBUG_MODE
from src.pelican_manager import Pelican
from src.websocket import connect_to_server
from src.events import EventEmitter
from src.discord_client import DiscordClient

REQUIRED_ENV_VARS = [
    'PANEL_API_URL',
    'PANEL_WSS_URL',
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

    # Get all servers
    pelican = Pelican()
    for server in pelican.get_servers():
        if DEBUG_MODE:
            print(server)
        connect_to_server(server)

    while True:
        time.sleep(1)

    # Initialize the event emitter
    event_emitter = EventEmitter()

    # Initialize the Discord client
    client = DiscordClient(event_emitter, int(os.getenv('DISCORD_CHANNEL')))
    client.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
