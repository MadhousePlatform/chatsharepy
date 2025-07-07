#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""

import os

from src.docker_manager import get_containers

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

    # Get all containers
    containers = get_containers()
    for container in containers:
        print(container.name)


if __name__ == "__main__":
    main()
