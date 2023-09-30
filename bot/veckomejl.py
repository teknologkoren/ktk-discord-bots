import random
import re

import discord

from instance.config import DISCORD_GUILD_ID, DISCORD_VECKOMEJL_CHANNEL_ID
from instance.config import VECKOMEJL_FOLDER_ID, VECKOMEJL_MAILING_LIST
from instance.config import BOARD_VECKOMEJL_LINK, DISCORD_BOARD_GUILD_ID, DISCORD_BOARD_VECKOMEJL_CHANNEL_ID

NUMBER_PATTERN = re.compile(r'\d+')
VECKOMEJL_MESSAGES = [
    "A new veckomejl just dropped:",
    "Äntligen! Veckomejlet är här:",
    "Veckans höjdpunkt är kommen; kom ihåg att läsa",
    "Nu är det här, direkt från styrelsen! Missa inte",
    "Ett nytt veckomejl finns nu i en inkorg nära dig:",
    "Du är oss alla kär, vår körklenod, vårt veckomejl:",
    "Sätt maskinen igång, du korist, sätt maskinen igång, du korist! Sätt på datorn och läs veckomejl:",
    "Fair Phyllis I saw sitting all alone, feeding her mind with the new veckomejl:",
    "Här är veck-, här är veck-, här är veckans veckomejl, där vilar ingen sorg:",
    (
        "Var redo, var redo, för nu ska mejlet fås! Var redo, var redo, för nu ska "
        "mejlet fås! Det gör gott i kroppen och i själen, känns ifrån hjässan långt "
        "ner i hälen. Läs, läs, läs, läs vårt nya veckomejl:"
    ),
    (
        "Av alla infoformer är det mejlet, som kan få mig varm med sin retrocharm. Oj, "
        "vad det blir hett av ordförandens vett! Tacka vet jag veckomejlet:"
    ),
]


# Check if the found email is a veckomejl, and if so send a veckomejl notification.
# Returns False if it wasn't a veckomejl, or True after sending the notification.
async def notify_if_veckomejl(bot, google_client, subject):
    if not 'veckomejl' in subject.lower():
        return False

    # Extract the week number from the subject line.
    match = NUMBER_PATTERN.search(subject)
    if not match:
        # If unsuccessful, it was probably not a veckomejl.
        return False
    week_number = match[0]

    # Check if there is a document to link to, and if so add a link button.
    result = await google_client.list_drive_folder(VECKOMEJL_FOLDER_ID)
    view = None

    # Loop through the files in the veckomejl Drive folder.
    for file in result['files']:
        if file['mimeType'] != 'application/vnd.google-apps.document':
            continue

        # We check that the number in the filename is the same instead of searching for
        # the week number in the filename, to avoid mixing up e.g. week 4 with week 40.
        match = NUMBER_PATTERN.search(file['name'])
        if match is None or match[0] != week_number:
            # This is not the document we're looking for.
            continue

        view = discord.ui.View(
            discord.ui.Button(
                emoji='<:docs:1095092193473089567>',
                label=subject.replace('[KTK]', '').strip(),
                url=file['webViewLink'],
            )
        )
        break

    # Send the notification!
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    channel = await guild.fetch_channel(DISCORD_VECKOMEJL_CHANNEL_ID)
    await channel.send(
        f"{random.choice(VECKOMEJL_MESSAGES)} **{subject}**",
        view=view
    )
    return True


async def check_for_email(bot, google_client):
    email = await google_client.get_new_email()
    if email is None:
        return
    if email['mailing_list'] is None or VECKOMEJL_MAILING_LIST not in email['mailing_list']:
        return

    if not await notify_if_veckomejl(bot, google_client, email.get('subject', None)):
        # If it wasn't a veckomejl, send a simpler notification with just the subject and sender.
        guild = await bot.fetch_guild(DISCORD_GUILD_ID)
        channel = await guild.fetch_channel(DISCORD_VECKOMEJL_CHANNEL_ID)
        await channel.send(
            f"Nytt mejl till aktiva: **{email.get('subject', None)}** från *{email.get('sender', None)}*"
        )


async def board_reminder(bot):
    if DISCORD_BOARD_GUILD_ID is None or DISCORD_BOARD_VECKOMEJL_CHANNEL_ID is None:
        print("Board Discord guild is not configured.")

    # Send the notification!
    if BOARD_VECKOMEJL_LINK is not None:
        view = discord.ui.View(
            discord.ui.Button(
                emoji='<:sheets:1157594624160976896>',
                label='Inför nästa veckomejl (levande dokument)',
                url=BOARD_VECKOMEJL_LINK,
            )
        )
    else:
        view = None

    guild = await bot.fetch_guild(DISCORD_BOARD_GUILD_ID)
    channel = await guild.fetch_channel(DISCORD_BOARD_VECKOMEJL_CHANNEL_ID)
    await channel.send(
        "Sista chansen att få med info i veckomejlet! 📧",
        view=view
    )
