import asyncio
import discord
import logging
import socketio
from datetime import datetime

import streque
from config import DISCORD_BOT_TOKEN, STREQUE_TOKEN, STREQUE_BASE_URL

# Logging for Discord bot.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Initialize Discord bot.
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# Initialize SocketIO client used to listen to events from Streque.
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

@sio.on('balance_change')
async def message(data):
    await streque.handle_balance_change(bot, data)

@sio.on('notification')
async def message(data):
    await streque.handle_notification(bot, data)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


bot.load_extension('quote')
bot.load_extension('song')

# Start the Discord bot and SocketIO connection to Streque.
loop = asyncio.get_event_loop()
loop.create_task(bot.start(DISCORD_BOT_TOKEN))
loop.create_task(sio.connect(STREQUE_BASE_URL, auth={'token': STREQUE_TOKEN}))
loop.run_forever()
