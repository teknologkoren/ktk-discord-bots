import sys
from datetime import datetime

from instance.config import DISCORD_POTATO_CHANNEL, DISCORD_GUILD_ID

videos = {
    1: ("https://www.youtube.com/watch?v=wmA5w-0xJ9s", "Guds knöl är kokt"),
    2: ("https://www.youtube.com/watch?v=RUrEDuKCiR8", "Förunderligt och välkokt"),
    3: ("https://www.youtube.com/watch?v=lnsOrivPYy0", "Ein knöl är min potät"),
    4: ("https://www.youtube.com/watch?v=K1PO-ns2lDw", "Sköna knöl"),
    5: ("https://www.youtube.com/watch?v=DTXO81iC-IY", "Över eld i vatten"),
    6: ("https://www.youtube.com/watch?v=qQrrYExkD9c", "Duka bord med kokt potatis"),
    7: ("https://www.youtube.com/watch?v=NRpALWQpB0g", "Knölman"),
    # TODO: add the rest of them
}

async def post(bot):
    now = datetime.now()
    if now.month != 12 or now.day > 24:
        print("Ingen knölvideo postades eftersom datumet ej är mellan 1-24 december.")
        return
    
    if now.day not in videos.keys():
        print(f"Ingen knölvideo postades eftersom ingen video hittades för lucka {now.day}.")
        return
    
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    channel = await guild.fetch_channel(DISCORD_POTATO_CHANNEL)
    await channel.send(f"Lucka {now.day} - {videos[now.day][1]}: {videos[now.day][0]}")