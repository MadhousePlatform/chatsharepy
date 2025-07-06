#!/usr/bin/env python3

"""
This is a test for the hello world program.
"""

import unittest
from io import StringIO
import sys
from hello import main

class TestHelloWorld(unittest.TestCase):
    """
    This is a test for the hello world program.
    """

    def test_main_output(self):
        """Test that main() prints 'Hello, World!'"""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Call the main function
            main()

            # Get the output
            output = captured_output.getvalue().strip()

            # Assert the expected output
            self.assertEqual(output, "Hello, World!")
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()
