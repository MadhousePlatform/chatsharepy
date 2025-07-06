#!/usr/bin/env python3

"""
Tests for the Chatshare application.
"""

import unittest
from io import StringIO
import sys
from chatshare import main

class TestChatshare(unittest.TestCase):
    """
    Tests for the Chatshare application.
    """

    def test_main_output(self):
        """Test that main() prints 'Welcome to Chatshare!'"""
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

if __name__ == '__main__':
    unittest.main()
