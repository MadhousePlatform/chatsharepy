import unittest
from unittest.mock import Mock, patch, MagicMock
from src.minecraft import parse_output, build_chat_message, build_event


class TestMinecraftIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for Minecraft integration tests."""
        self.test_server = {
            'external_id': 'testserver',
            'identifier': 'test-server-id',
            'uuid': 'test-server-uuid',
            'name': 'Test Minecraft Server'
        }

    @patch('src.minecraft.broadcast_to_all')
    def test_build_chat_message(self, mock_broadcast):
        """Test building and broadcasting chat messages."""
        server_name = 'testserver'
        origin = self.test_server
        time = '14:30:00'
        user = 'TestPlayer'
        message = 'Hello, world!'
        
        build_chat_message(server_name, origin, time, user, message)
        
        # Verify broadcast was called with correct data
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        
        # Check that origin and except_origin parameters are correct
        self.assertEqual(call_args[0][0], origin)  # First argument is origin
        self.assertEqual(call_args[1]['except_origin'], True)  # except_origin=True
        
        # Check that the data contains the expected tellraw command
        data = call_args[0][1]  # Second argument is data
        self.assertIn('tellraw @a', data)
        self.assertIn(f'mc:{server_name}', data)
        self.assertIn(user, data)
        self.assertIn(message, data)

    @patch('src.minecraft.broadcast_to_all')
    def test_build_event_advancement(self, mock_broadcast):
        """Test building and broadcasting advancement events."""
        server_name = 'testserver'
        origin = self.test_server
        time = '14:30:00'
        user = 'TestPlayer'
        advancement = 'Stone Age'
        
        build_event('advancement', server_name, origin, time, user, advancement)
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        
        # Check the data contains advancement information
        data = call_args[0][1]
        self.assertIn('tellraw @a', data)
        self.assertIn(f'mc:{server_name}', data)
        self.assertIn(user, data)
        self.assertIn('made the advancement', data)
        self.assertIn(advancement, data)

    @patch('src.minecraft.src.regexes')
    @patch('src.minecraft.build_chat_message')
    def test_parse_output_chat_message(self, mock_build_chat, mock_regexes):
        """Test parsing chat message output."""
        # Mock regex for testserver
        mock_regex = Mock()
        mock_regex.match.return_value = Mock()
        mock_regex.match.return_value.groupdict.return_value = {
            'server': 'testserver',
            'user': 'TestPlayer',
            'message': 'Hello, world!',
            'time': '14:30:00'
        }
        
        # Set up mock regexes
        mock_server_regexes = {'message': mock_regex}
        setattr(mock_regexes, 'testserver', mock_server_regexes)
        
        test_output = '[testserver] [14:30:00] <TestPlayer> Hello, world!'
        
        parse_output(test_output, self.test_server)
        
        # Verify chat message was built
        mock_build_chat.assert_called_once_with(
            'testserver',
            self.test_server,
            '02:30PM',  # Time should be converted
            'TestPlayer',
            'Hello, world!'
        )

    @patch('src.minecraft.src.regexes')
    @patch('src.minecraft.build_event')
    def test_parse_output_join_event(self, mock_build_event, mock_regexes):
        """Test parsing player join events."""
        # Mock regex for join event
        mock_regex = Mock()
        mock_regex.match.return_value = Mock()
        mock_regex.match.return_value.groupdict.return_value = {
            'server': 'testserver',
            'user': 'TestPlayer',
            'time': '14:30:00'
        }
        
        # Set up mock regexes
        mock_server_regexes = {'join': mock_regex}
        setattr(mock_regexes, 'testserver', mock_server_regexes)
        
        test_output = '[testserver] [14:30:00] TestPlayer joined the game'
        
        parse_output(test_output, self.test_server)
        
        # Verify join event was built
        mock_build_event.assert_called_once_with(
            'join',
            'testserver',
            self.test_server,
            '02:30PM',
            'TestPlayer',
            'joined the server.'
        )

    def test_time_conversion(self):
        """Test time format conversion."""
        from src.minecraft import time_cvt
        
        # Test valid time conversion
        result = time_cvt('14:30:00')
        self.assertEqual(result, '02:30PM')
        
        # Test invalid time (should return original)
        result = time_cvt('invalid-time')
        self.assertEqual(result, 'invalid-time')
        
        # Test None input
        result = time_cvt(None)
        self.assertIsNone(result)


class TestMinecraftWebSocketIntegration(unittest.TestCase):
    """Integration tests for Minecraft WebSocket functionality."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.test_server = {
            'external_id': 'gameserver',
            'identifier': 'game-server-id',
            'uuid': 'game-server-uuid',
            'name': 'Game Server'
        }

    @patch('src.broadcast.websock')
    @patch('src.minecraft.broadcast_to_all')
    def test_minecraft_chat_broadcast_integration(self, mock_broadcast, mock_websock):
        """Test integration between Minecraft chat parsing and WebSocket broadcasting."""
        # Set up mock websocket
        mock_websocket = Mock()
        mock_websocket.sock = Mock()
        mock_websocket.sock.connected = True
        
        mock_websock.__len__.return_value = 1
        mock_websock.__iter__.return_value = iter([
            {'socket': mock_websocket, 'name': 'otherserver'}
        ])
        
        # Test chat message
        server_name = 'gameserver'
        origin = self.test_server
        time = '14:30:00'
        user = 'Player1'
        message = 'Test message'
        
        # Build chat message (this calls broadcast_to_all internally)
        build_chat_message(server_name, origin, time, user, message)
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        
        # Get the actual broadcast call arguments
        call_args = mock_broadcast.call_args
        origin_arg = call_args[0][0]
        data_arg = call_args[0][1]
        except_origin_arg = call_args[1]['except_origin']
        
        # Verify the arguments
        self.assertEqual(origin_arg, origin)
        self.assertTrue(except_origin_arg)
        self.assertIn('tellraw @a', data_arg)
        self.assertIn(user, data_arg)
        self.assertIn(message, data_arg)


if __name__ == '__main__':
    unittest.main()