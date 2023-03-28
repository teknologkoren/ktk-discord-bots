import re
from datetime import datetime

import discord
from discord import commands, option
import streque
from config import DISCORD_BOT_TOKEN

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


bot.load_extension('quote')
bot.run(DISCORD_BOT_TOKEN)
