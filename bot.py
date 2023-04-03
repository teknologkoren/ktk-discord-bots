import asyncio
import discord
import logging
import socketio
from datetime import datetime

import streque
from config import CHOIR_BOT_TOKEN, STREQUE_BOT_TOKEN, STREQUE_TOKEN, STREQUE_BASE_URL

# Logging for Discord bot.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Initialize Discord bots.
streque_bot = discord.Bot(intents=discord.Intents.default())
choir_bot = discord.Bot(intents=discord.Intents.default())

# Initialize SocketIO client used to listen to events from Streque.
sio = socketio.AsyncClient(logger=True, engineio_logger=True)


@sio.on('balance_change')
async def message(data):
    await streque.handle_balance_change(streque_bot, data)


@sio.on('notification')
async def message(data):
    await streque.handle_notification(streque_bot, data)


@streque_bot.event
async def on_ready():
    print(f'We have logged in as {streque_bot.user}')


@choir_bot.event
async def on_ready():
    print(f'We have logged in as {choir_bot.user}')


streque_bot.load_extension('quote')
choir_bot.load_extension('song')

# Start the Discord bot and SocketIO connection to Streque.
loop = asyncio.get_event_loop()
loop.create_task(streque_bot.start(STREQUE_BOT_TOKEN))
loop.create_task(choir_bot.start(CHOIR_BOT_TOKEN))
loop.create_task(sio.connect(STREQUE_BASE_URL, auth={'token': STREQUE_TOKEN}))
loop.run_forever()
