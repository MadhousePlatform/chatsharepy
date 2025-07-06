#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
from io import StringIO
from src.chatshare import main

class TestChatshare(unittest.TestCase):
    """
    Tests for the Chatshare application.
    """

    @patch('src.chatshare.get_containers')
    def test_main_output(self, mock_get_containers):
        """Test that main() prints 'Welcome to Chatshare!'"""
        # Configure mock to return empty list
        mock_get_containers.return_value = []

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output
            self.assertEqual(output, "Welcome to Chatshare!")
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

    @patch('src.chatshare.get_containers')
    def test_main_with_containers(self, mock_get_containers):
        """Test main function with containers."""
        # Create mock containers
        mock_container1 = Mock()
        mock_container1.name = "app-container"

        mock_container2 = Mock()
        mock_container2.name = "db-container"

        mock_get_containers.return_value = [mock_container1, mock_container2]

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output
            expected_lines = [
                "Welcome to Chatshare!",
                "app-container",
                "db-container"
            ]
            actual_lines = output.split('\n')

            self.assertEqual(len(actual_lines), 3)
            for i, expected in enumerate(expected_lines):
                self.assertEqual(actual_lines[i], expected)

        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

    @patch('src.chatshare.get_containers')
    def test_main_with_no_containers(self, mock_get_containers):
        """Test main function with no containers."""
        # Configure mock to return empty list
        mock_get_containers.return_value = []

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output (only welcome message)
            self.assertEqual(output, "Welcome to Chatshare!")

        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

    @patch('src.chatshare.get_containers')
    def test_main_with_docker_error(self, mock_get_containers):
        """Test main function when Docker manager raises an error."""
        # Configure mock to raise an exception
        mock_get_containers.side_effect = Exception("Docker connection failed")

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function and expect it to raise the exception
            with self.assertRaises(Exception) as context:
                main()

            self.assertEqual(str(context.exception), "Docker connection failed")

        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

class TestIntegration(unittest.TestCase):
    """
    Integration tests for the complete application flow.
    """

    @patch('src.docker_manager.client')
    def test_full_application_flow(self, mock_client):
        """Test the complete flow from main() to Docker manager."""
        # Create mock containers
        mock_container1 = Mock()
        mock_container1.name = "web-app"
        mock_container1.status = "running"

        mock_container2 = Mock()
        mock_container2.name = "database"
        mock_container2.status = "running"

        mock_client.containers.list.return_value = [mock_container1, mock_container2]

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output
            expected_lines = [
                "Welcome to Chatshare!",
                "web-app",
                "database"
            ]
            actual_lines = output.split('\n')

            self.assertEqual(len(actual_lines), 3)
            for i, expected in enumerate(expected_lines):
                self.assertEqual(actual_lines[i], expected)

            # Verify Docker client was called
            mock_client.containers.list.assert_called_once()

        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()
