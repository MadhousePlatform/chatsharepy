"""
Docker manager module.
"""

import docker

client = docker.from_env()

def get_containers():
    """
    Get all containers.
    """
    containers = client.containers.list()
    return containers
