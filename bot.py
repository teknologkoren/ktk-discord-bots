import asyncio
import socketio
import discord
import pprint
from config import DISCORD_BOT_TOKEN, STREQUE_TOKEN, STREQUE_BASE_URL

from datetime import datetime

import streque

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
sio = socketio.AsyncClient(logger=True, engineio_logger=True)
pp = pprint.PrettyPrinter(indent=2)

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

async def main():
    await sio.connect(STREQUE_BASE_URL, auth={'token': STREQUE_TOKEN})
    await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())
