#!/usr/bin/env python3

import unittest
from io import StringIO
import sys
from hello import main

class TestHelloWorld(unittest.TestCase):
    
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
    
    def test_main_returns_none(self):
        """Test that main() returns None (implicit return)"""
        result = main()
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 