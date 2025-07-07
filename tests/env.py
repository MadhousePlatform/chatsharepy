#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import unittest
import os

class TestEnvironmentVariablesLoaded(unittest.TestCase):
    """
    Tests that we have environment variables loaded.
    """


    def test_server_api_is_correct(self):
        """Test that SERVER_API is set to the correct value."""
        self.assertEqual(os.environ['SERVER_API'], 'https://peli.sketchni.uk/')


if __name__ == '__main__':
    unittest.main()
