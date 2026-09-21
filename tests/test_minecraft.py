import unittest
from unittest.mock import patch

from src.minecraft import build_discord_chat_message, parse_output


class TestBuildDiscordChatMessage(unittest.TestCase):
    @patch('src.minecraft.broadcast_to_all')
    def test_broadcasts_discord_message_to_all_minecraft_servers(self, mock_broadcast_to_all):
        discord_message = {
            'message': 'Hello from Discord',
            'sender': 'DiscordUser',
            'source': 'discord',
        }

        build_discord_chat_message(discord_message)

        mock_broadcast_to_all.assert_called_once()
        origin, data, msg = mock_broadcast_to_all.call_args.args
        kwargs = mock_broadcast_to_all.call_args.kwargs

        # The origin must never match a real Minecraft server's external_id,
        # so broadcast_to_all's except_origin check sends to every server.
        self.assertEqual(origin, {'external_id': 'discord'})
        self.assertTrue(kwargs.get('except_origin'))
        self.assertIn('tellraw @a', data)
        self.assertIn('DiscordUser', data)
        self.assertIn('Hello from Discord', data)
        self.assertIn('discord', data.lower())
        self.assertIn('DiscordUser', msg)
        self.assertIn('Hello from Discord', msg)

    @patch('src.minecraft.broadcast_to_all')
    def test_ignores_chat_events_not_sourced_from_discord(self, mock_broadcast_to_all):
        minecraft_message = {
            'message': 'Hello from Minecraft',
            'sender': 'MinecraftUser',
            'source': 'minecraft',
        }

        build_discord_chat_message(minecraft_message)

        mock_broadcast_to_all.assert_not_called()


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
