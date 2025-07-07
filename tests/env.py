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
        """Test that PANEL_API_URL is set to the correct value."""
        self.assertEqual(os.environ['PANEL_API_URL'], 'http://example.com/api')


if __name__ == '__main__':
    unittest.main()
