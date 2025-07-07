#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""

import os
from src.docker_manager import get_containers

if os.environ['PANEL_API_URL'] is None or os.environ['PANEL_API_URL'] == "":
    raise Exception("Please set the PANEL_API_URL environment variable.")
if os.environ['PANEL_APPLICATION_KEY'] is None or os.environ['PANEL_APPLICATION_KEY'] == "":
    raise Exception("Please set the PANEL_APPLICATION_KEY environment variable.")
if os.environ['PANEL_CLIENT_KEY'] is None or os.environ['PANEL_CLIENT_KEY'] == "":
    raise Exception("Please set the PANEL_CLIENT_KEY environment variable.")
if os.environ['DISCORD_TOKEN'] is None or os.environ['DISCORD_TOKEN'] == "":
    raise Exception("Please set the DISCORD_TOKEN environment variable.")
if os.environ['DISCORD_CHANNEL'] is None or os.environ['DISCORD_CHANNEL'] == "":
    raise Exception("Please set the DISCORD_CHANNEL environment variable.")


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
