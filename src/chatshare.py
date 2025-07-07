#!/usr/bin/env python3

"""
Chatshare - A chat sharing application.
"""

from dotenv import load_dotenv
from src.docker_manager import get_containers


load_dotenv()

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
