#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""
import os

from src.debug import parse_args
from src.pelican_manager import Pelican
from src.websockets import Websockets
from src.discord_client import DiscordClient
from src.events import EventEmitter

REQUIRED_ENV_VARS = [
    'PANEL_ORIGIN_URL',
    'PANEL_API_URL',
    'PANEL_WSS_URL',
    'WINGS_TOKEN',
    'PANEL_APPLICATION_KEY',
    'PANEL_CLIENT_KEY',
    'DISCORD_TOKEN',
    'DISCORD_CHANNEL',
]

for var in REQUIRED_ENV_VARS:
    value = os.getenv(var)
    if not value:  # catches None and empty string
        raise ValueError(f"Please set the {var} environment variable.")

def main():
    """
    Main entry point for the Chatshare application.
    """
    parse_args()
    print("Welcome to Chatshare!")

    # Get all servers
    pelican = Pelican()
    for server in pelican.get_servers():
        print(f"server: {server.get('external_id')} - {server.get('name')} - {server.get('description')}")
        Websockets(server).connect_to_server(server)

    # Initialise the event emitter
    event_emitter = EventEmitter()
    discord = DiscordClient(event_emitter, int(os.getenv('DISCORD_CHANNEL')))
    # Initialise the Discord client
    discord.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
