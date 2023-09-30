import logging
from datetime import datetime

import aiocron
import asyncio
import discord
import socketio

from bot import (
    assign_groups,
    balance_change,
    birthday,
    nickname_emoji,
    notifications,
    player,
    veckomejl,
)
from bot.clients import google, rotary_phone
from instance.config import CHOIR_BOT_TOKEN, STREQUE_BOT_TOKEN, STREQUE_TOKEN, STREQUE_BASE_URL

# Logging for Discord bot.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# A custom subclass of `discord.Bot` is required in order to listen manually
# to some interactions without catching them all. And this in turn is needed
# for responding to button clicks that no longer have a corresponding View
# (for example due to the bot having been restarted since the view was created).
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

            elif custom_id.startswith('call-'):
                song_id = int(custom_id[len('call-'):])
                song = self.get_cog('Song').by_id[song_id]
                await rotary_phone.play_note(interaction, song['tones'])
                return

        await super().on_interaction(interaction)

    async def on_member_join(self, member):
        await assign_groups.set_extra_roles(member, self)


# Initialize Discord bots.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
streque_bot = CustomBot(intents=intents)

if CHOIR_BOT_TOKEN:
    intents = discord.Intents.default()
    intents.message_content = True
    choir_bot = CustomBot(intents=intents)
else:
    # To make testing easier, do not require two separate bot accounts.
    choir_bot = streque_bot

# Initialize SocketIO client used to listen to events from Streque.
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# Initialize Google API client.
google_client = google.GoogleAPIClient()


@sio.on('notification')
async def message(data):
    await notifications.handle_notification(streque_bot, data)


@sio.on('balance_change')
async def message(data):
    await balance_change.handle_balance_change(streque_bot, data)
    await nickname_emoji.handle_balance_change(streque_bot, data)


# Run every ten minutes with offset 1, i.e. XX:01, XX:11, XX:21, etc
# to check whether any nickname emojis need updating.
@aiocron.crontab('1/10 * * * *')
async def check_emoji_updates():
    print(f"{datetime.now()} Periodic nickname emoji sync.")
    await nickname_emoji.periodic_update(streque_bot)


# Run every minute to check for new emails.
@aiocron.crontab('*/1 * * * *')
async def check_email():
    print(f"{datetime.now()} Periodic email check.")
    await veckomejl.check_for_email(choir_bot, google_client)


# Run every Sunday at 10 AM to remind the board to fill out the weekly email document
@aiocron.crontab('0 10 * * 0')
async def weekly_email_reminder():
    print(f"{datetime.now()} Reminding the board about the weekly email.")
    await veckomejl.board_reminder(choir_bot)


# Run noon every day to check for birthdays.
@aiocron.crontab('0 12 * * *')
async def check_birthdays():
    print(f"{datetime.now()} It is midnight, let's check if it is someone's birthday!")
    await birthday.congratulate(streque_bot)


@streque_bot.event
async def on_ready():
    print(f'We have logged in as {streque_bot.user}')


@choir_bot.event
async def on_ready():
    print(f'We have logged in as {choir_bot.user}')


streque_bot.load_extension('bot.quote')
choir_bot.load_extension('bot.song')
choir_bot.load_extension('bot.club')

# Start the Discord bot and SocketIO connection to Streque.
loop = asyncio.get_event_loop()
loop.create_task(streque_bot.start(STREQUE_BOT_TOKEN))
if CHOIR_BOT_TOKEN: # Only start the second bot if we have credentials for it.
    loop.create_task(choir_bot.start(CHOIR_BOT_TOKEN))
loop.create_task(sio.connect(STREQUE_BASE_URL, auth={'token': STREQUE_TOKEN}))
loop.run_forever()
