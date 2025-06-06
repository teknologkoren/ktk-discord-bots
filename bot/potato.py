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
    8: ("https://www.youtube.com/watch?v=gM8QRADdt0I", "O helga knöl"),
    9: ("https://www.youtube.com/watch?v=zeiy8swD2uA", "Veni Potatisen"),
    10: ("https://www.youtube.com/watch?v=qIg0S5l95-s", "Kommer icke Knölof Tryggvasson"),
    11: ("https://www.youtube.com/watch?v=iB0WVRsoka4", "Staffan var en potatisdräng"),
    12: ("https://www.youtube.com/watch?v=zRNf02-WDOI", "God potatis i detta skal"),
    13: ("https://www.youtube.com/watch?v=QbcdeCrNIqo", "Strålande jordeknöl"),
    14: ("https://www.youtube.com/watch?v=FqvhXl_by_Y", "Sankta Potatis"),
    15: ("https://www.youtube.com/watch?v=LHABeMFSDKg", "Fååunnelig ädh khåågge"),
    16: ("https://www.youtube.com/watch?v=uW0rnR69IDM", "God rest ye merry Potato"),
    17: ("https://www.youtube.com/watch?v=lQ-Ci8y__dQ", "Det strålar en rotfrukt"),
    18: ("https://www.youtube.com/watch?v=cZD-HOEMYhU", "Sådan är Potatisplantan"),
    19: ("https://www.youtube.com/watch?v=-4zk195PcSU", "Potatisen"),
    20: ("https://www.youtube.com/watch?v=Fb8QtmNmOXo", "Det är en rot utsprungen"),
    21: ("https://www.youtube.com/watch?v=2PapRwhMy9k", "Knöl, Potatis, Tenorvän"),
    22: ("https://www.youtube.com/watch?v=3eOWZargoY0", "Gul Gul"),
    23: ("https://www.youtube.com/watch?v=CxTJJTNfz5s", "Nu kokas tusen juleknöl"),
    24: ("https://www.youtube.com/watch?v=3Ek40aWEulo", "Knölevangeliet"),
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
