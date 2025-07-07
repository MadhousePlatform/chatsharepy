import unittest
import os

class TestEnvironmentVariablesLoaded(unittest.TestCase):
    def test_server_api_is_correct(self):
        self.assertEqual(os.environ['SERVER_API'], 'https://peli.sketchni.uk/')


if __name__ == '__main__':
    unittest.main()
