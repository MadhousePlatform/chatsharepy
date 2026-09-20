import unittest

from src.regexes import atm10


class TestAtm10MessageRegex(unittest.TestCase):
    def test_message_matches_single_closing_angle_bracket(self):
        line = ("[atm10] [19:41:36] [Server thread/INFO] [minecraft/MinecraftServer]: "
                "<Sketch> Hello world!")

        match = atm10["message"].match(line)

        self.assertIsNotNone(match)
        self.assertEqual(match.group("user"), "Sketch")
        self.assertEqual(match.group("message"), "Hello world!")

    def test_message_pattern_matches_single_angle_bracket_like_its_siblings(self):
        # The join/part/ban/pardon/advancement patterns in the same atm10 dict
        # use a single closing angle bracket ("> ") after the prefix. The
        # message pattern should be consistent with them rather than requiring
        # a second ">" that a real ATM10 chat line never sends.
        self.assertIn("> ", atm10["message"].pattern)
        self.assertNotIn(">> ", atm10["message"].pattern)


if __name__ == "__main__":
    unittest.main()
