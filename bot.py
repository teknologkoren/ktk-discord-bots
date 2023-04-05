import logging
from datetime import datetime

import aiocron
import asyncio
import discord
import socketio

import balance_change
import birthday
import notifications
import player
from config import CHOIR_BOT_TOKEN, STREQUE_BOT_TOKEN, STREQUE_TOKEN, STREQUE_BASE_URL

# Logging for Discord bot.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# A custom subclass of `discord.Bot`` is required in order to listen manually
# to some interactions without catching them all. And this in turn is needed
# for responding to button clicks that no longer have a corresponding View.
class CustomBot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)

    async def on_interaction(self, interaction):
        custom_id = interaction.custom_id
        if custom_id:

            if custom_id.startswith('notification-'):
                await notifications.mark_read_callback(interaction)
                return

            elif custom_id.startswith('ta-ton-'):
                song_id = int(custom_id[len('ta-ton-'):])
                song = self.get_cog('Song').by_id[song_id]
                await player.play_note(interaction, self, song['tones'])
                return

        await super().on_interaction(interaction)


# Initialize Discord bots.
intents = discord.Intents.default()
intents.message_content = True
streque_bot = CustomBot(intents=intents)
choir_bot = CustomBot(intents=intents)

# Initialize SocketIO client used to listen to events from Streque.
sio = socketio.AsyncClient(logger=True, engineio_logger=True)


@sio.on('balance_change')
async def message(data):
    await balance_change.handle_balance_change(streque_bot, data)


@sio.on('notification')
async def message(data):
    await notifications.handle_notification(streque_bot, data)


@aiocron.crontab('0 0 * * *')
async def check_birthdays():
    print(f"{datetime.now()} It is midnight, let's check if it is someone's birthday!")
    await birthday.congratulate(streque_bot)


@streque_bot.event
async def on_ready():
    print(f'We have logged in as {streque_bot.user}')


@choir_bot.event
async def on_ready():
    print(f'We have logged in as {choir_bot.user}')


streque_bot.load_extension('quote')
choir_bot.load_extension('song')
choir_bot.load_extension('club')

# Start the Discord bot and SocketIO connection to Streque.
loop = asyncio.get_event_loop()
loop.create_task(streque_bot.start(STREQUE_BOT_TOKEN))
loop.create_task(choir_bot.start(CHOIR_BOT_TOKEN))
loop.create_task(sio.connect(STREQUE_BASE_URL, auth={'token': STREQUE_TOKEN}))
loop.run_forever()
