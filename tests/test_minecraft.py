import json
import unittest
from unittest.mock import patch

from src.debug import debug_state
from src.minecraft import build_chat_message, build_discord_chat_message, parse_output


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
    def test_does_not_relay_message_back_to_discord(self, mock_broadcast_to_all):
        """
        A Discord-originated message must not be echoed back to Discord by
        the bot: broadcast_to_all must be told to skip the Discord relay.
        """
        discord_message = {
            'message': 'Hello from Discord',
            'sender': 'DiscordUser',
            'source': 'discord',
        }

        build_discord_chat_message(discord_message)

        kwargs = mock_broadcast_to_all.call_args.kwargs
        self.assertFalse(kwargs.get('relay_to_discord', True))

    @patch('src.minecraft.broadcast_to_all')
    def test_ignores_chat_events_not_sourced_from_discord(self, mock_broadcast_to_all):
        minecraft_message = {
            'message': 'Hello from Minecraft',
            'sender': 'MinecraftUser',
            'source': 'minecraft',
        }

        build_discord_chat_message(minecraft_message)

        mock_broadcast_to_all.assert_not_called()

    @patch('src.minecraft.broadcast_to_all')
    def test_escapes_malicious_discord_message_in_tellraw_payload(self, mock_broadcast_to_all):
        """
        A Discord message crafted to break out of the tellraw JSON string
        must not be able to inject extra tellraw components (e.g. a
        clickEvent that runs an arbitrary command on connected servers).
        """
        malicious_message = {
            'message': 'hi"},{"clickEvent":{"action":"run_command",'
                        '"value":"/op Evil"},"text":"',
            'sender': 'DiscordUser',
            'source': 'discord',
        }

        build_discord_chat_message(malicious_message)

        _, data, _ = mock_broadcast_to_all.call_args.args
        payload = data[len('tellraw @a '):].rstrip('\n')

        # The whole payload must still be valid JSON with exactly the three
        # legitimate components (prefix, sender, message) that
        # build_discord_chat_message constructs: the attacker-controlled
        # text must land inside the message component's "text" field as
        # inert data, not as an extra injected component.
        components = json.loads(payload)
        self.assertEqual(len(components), 3)
        self.assertEqual(components[2]['text'], malicious_message['message'])

    @patch('src.minecraft.broadcast_to_all')
    def test_escapes_malicious_minecraft_message_in_tellraw_payload(self, mock_broadcast_to_all):
        """
        The same injection risk applies to Minecraft-sourced chat text fed
        into build_chat_message.
        """
        malicious_text = ('hi"},{"clickEvent":{"action":"run_command",'
                           '"value":"/op Evil"},"text":"')

        build_chat_message(
            'vanilla', {'external_id': 'vanilla'}, '19:41:36', 'Steve', malicious_text,
        )

        _, data, _ = mock_broadcast_to_all.call_args.args
        payload = data[len('tellraw @a '):].rstrip('\n')

        components = json.loads(payload)
        self.assertEqual(len(components), 3)
        self.assertEqual(components[2]['text'], malicious_text)


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


class TestParseOutputLogging(unittest.TestCase):
    """
    Representative cases proving parse_output logs at the right level via
    the shared logger, rather than printing to stdout.
    """

    def setUp(self):
        self.original_debug_state = debug_state['enabled']
        debug_state['enabled'] = True

    def tearDown(self):
        debug_state['enabled'] = self.original_debug_state

    @patch("src.minecraft.logger")
    def test_invalid_server_object_logs_an_error(self, mock_logger):
        result = parse_output("some output", {"external_id": 123})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "Invalid server object", mock_logger.error.call_args.args[0])

    @patch("src.minecraft.logger")
    def test_unknown_server_logs_a_debug_message(self, mock_logger):
        result = parse_output("hello", {"external_id": "no-such-server"})

        self.assertIsNone(result)
        mock_logger.debug.assert_any_call(
            "No regexes found for server: %s", "no-such-server")


class TestParseOutputLoggingWithoutDebugMode(unittest.TestCase):
    """
    Error paths in parse_output must log unconditionally, not only when
    debug mode is enabled, so real error conditions still reach syslog in
    normal production operation.
    """

    def setUp(self):
        self.original_debug_state = debug_state['enabled']
        debug_state['enabled'] = False

    def tearDown(self):
        debug_state['enabled'] = self.original_debug_state

    @patch("src.minecraft.logger")
    def test_invalid_server_object_logs_an_error_without_debug_mode(self, mock_logger):
        result = parse_output("some output", {"external_id": 123})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "Invalid server object", mock_logger.error.call_args.args[0])

    @patch("src.minecraft.logger")
    def test_missing_external_id_logs_an_error_without_debug_mode(self, mock_logger):
        result = parse_output("some output", {"external_id": ""})

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        self.assertIn(
            "external_id missing", mock_logger.error.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
