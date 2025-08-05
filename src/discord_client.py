"""
Discord client class
"""

import discord
from src.log import logger
from src.events import EventEmitter

class DiscordClient(discord.Client):
    """
    Discord client class
    """

    def __init__(self, event_emitter: EventEmitter, channel_id: int):
        """
        Initialize the Discord client

        Args:
            event_emitter: EventEmitter instance
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        # Get the channel ID from the environment variable
        self.watch_channel_id = channel_id

        # Set the event emitter
        self.event_emitter = event_emitter
        self.event_emitter.on('chat', self.on_chat_message)

        logger.debug(f"Watching channel ID: {self.watch_channel_id}")
        super().__init__(intents=intents)

    # Discord client events

    async def on_ready(self):
        """
        On ready event

        Args:
            self: DiscordClient instance
        """
        logger.info(f'[Discord] Connected to Discord as {self.user}')

    async def on_message(self, message):
        """
        On message event

        Args:
            message: Message object
        """
        # Only respond to messages in the specified channel
        if message.channel.id != self.watch_channel_id:
            return

        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Emit the message to the event emitter
        message_data = {
            'message': message.content,
            'sender': message.author.name,
            'source': 'discord'
        }
        logger.debug(f"Received message: {message_data} from "
                     f"{message.author.name} in {message.channel.name} channel")
        self.event_emitter.emit('chat', message_data)

    # Event emitter handlers
    async def on_chat_message(self, message: dict):
        """
        On chat message event

        Args:
            message: Message data
        """
        if message['source'] != 'discord':
            # Send the message to the channel
            msg = f"[{message['source']}] <{message['sender']}> {message['message']}"

            logger.debug(f"Sending message: {msg}")
            await self.watch_channel.send(msg)
