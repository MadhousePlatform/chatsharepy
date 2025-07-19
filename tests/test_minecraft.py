import unittest
from unittest.mock import patch

from src.minecraft import parse_output


class TestParseOutput(unittest.TestCase):
    def test_parse_output_regular_line(self):
        result = parse_output("[vanilla] [19:41:36] [Server thread/INFO]: <Sketch> Hello world!",
                              {"external_id": "vanilla"})
        # Assuming parse_output returns processed text if successful
        self.assertIsNotNone(result)
        self.assertIn("Hello world", result)

    def test_parse_output_empty_line(self):
        result = parse_output("", {"external_id": "vanilla"})
        self.assertFalse(result)  # Or adapt if your function behaves differently

    def test_parse_output_with_special_event(self):
        # If parse_output triggers something special for keywords
        result = parse_output("[vanilla] [19:19:02] [Server thread/INFO]: Player has made the advancement [dookie pie]!",
                              {"external_id": "vanilla"})
        self.assertIn("dookie pie", result)


if __name__ == "__main__":
    unittest.main()
