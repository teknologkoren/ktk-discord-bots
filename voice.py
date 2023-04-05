import asyncio
import discord
import math
import struct
from functools import cache


steps_from_A = {
    'A': 0,
    'B': 2,
    'C': 3,
    'D': 5,
    'E': 7,
    'F': 8,
    'G': 10,
}


@cache
def note_to_frequency(note: str):
    offset = steps_from_A[note[0]]
    if len(note) > 1:
        if note[1] == '#':
            offset += 1
        elif note[1] == 'b':
            offset -= 1
    
    return 440 * (2 ** (offset/12))


async def play_note(interaction, bot, notes):
    channel = interaction.user.voice.channel
    if channel is None:
        return
    
    client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if client:
        if client.channel != channel:
            await client.disconnect()
            client = None
    
    if not client:
        client = await channel.connect()

    client.play(NotePlayer(notes))
    await interaction.response.edit_message()


class NotePlayer(discord.AudioSource):
    def __init__(self, notes):
        self.i = 0
        self.n = 0
        self.notes = notes
    
    def read(self):
        if self.i >= 48_000:
            self.i = 0
            self.n += 1
            if self.n >= len(self.notes):
                return bytes()

        frame = bytearray()

        for _ in range(960):
            amplitude = 2**14 + round(
                2**13 *
                math.sin(
                    self.i * 2 * math.pi *
                    note_to_frequency(self.notes[self.n]) / 48_000))

            b1, b2 = struct.pack('<H', amplitude)
            frame.append(b1) # Channel 1
            frame.append(b2)
            frame.append(b1) # Channel 2
            frame.append(b2)
            self.i += 1
        
        return bytes(frame)
    
    def is_opus(self):
        return False
