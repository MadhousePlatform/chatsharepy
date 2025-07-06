#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""

from docker_manager import get_containers

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
