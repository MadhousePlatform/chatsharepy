#!/usr/bin/env python3

"""
Tests for the Docker manager module.
"""

import unittest
from unittest.mock import Mock, patch
from docker_manager import get_containers

class TestDockerManager(unittest.TestCase):
    """
    Tests for the Docker manager module.
    """

    @patch('docker_manager.client')
    def test_get_containers_success(self, mock_client):
        """Test successful container retrieval."""
        # Create mock containers
        mock_container1 = Mock()
        mock_container1.name = "test-container-1"
        mock_container1.status = "running"

        mock_container2 = Mock()
        mock_container2.name = "test-container-2"
        mock_container2.status = "stopped"

        # Configure mock client
        mock_client.containers.list.return_value = [mock_container1, mock_container2]

        # Call the function
        containers = get_containers()

        # Assertions
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0].name, "test-container-1")
        self.assertEqual(containers[1].name, "test-container-2")
        mock_client.containers.list.assert_called_once()

    @patch('docker_manager.client')
    def test_get_containers_empty(self, mock_client):
        """Test container retrieval when no containers exist."""
        # Configure mock client to return empty list
        mock_client.containers.list.return_value = []

        # Call the function
        containers = get_containers()

        # Assertions
        self.assertEqual(len(containers), 0)
        mock_client.containers.list.assert_called_once()

    @patch('docker_manager.client')
    def test_get_containers_docker_error(self, mock_client):
        """Test handling of Docker connection errors."""
        # Configure mock client to raise an exception
        mock_client.containers.list.side_effect = Exception("Docker connection failed")

        # Call the function and expect it to raise the exception
        with self.assertRaises(Exception) as context:
            get_containers()

        self.assertEqual(str(context.exception), "Docker connection failed")
