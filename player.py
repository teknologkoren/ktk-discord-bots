import asyncio
import math
import struct
import sys
from functools import cache

import discord

from config import DISCORD_GUILD_ID

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
    user = interaction.user

    if interaction.guild is None:
        guild = await bot.fetch_guild(DISCORD_GUILD_ID)
        member = await guild.fetch_member(user.id)

        if member.voice is None:
            await interaction.response.send_message(
                content="Gå in i en röstkanal i Kongl. Teknologkörens server och försök igen, "
                    "så följer jag efter dig och tar ton där!",
                ephemeral=True)
            return
        else:
            user = member

    if user.voice is None:
        await interaction.response.send_message(
            content="Gå in i en röstkanal och försök igen, så följer jag efter dig och tar ton där!",
            ephemeral=True)
        return

    # If the bot is already in a voice channel, get the client.
    client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    # Check if the bot is in the same channel as the calling user.
    channel = user.voice.channel
    if client and client.is_connected():
        if client.channel != channel:
            await client.disconnect()
            client = None

    # Connect to the voice channel that the calling user is in.
    if not client:
        client = await channel.connect()

        # Wait a short duration to not have the notes start playing directly after
        # the connect sound.
        await asyncio.sleep(0.5)

    # Play the note sequence.
    client.play(NotePlayer(notes))

    # Respond to the interaction to let Discord know it was successful.
    await interaction.response.edit_message()

    # Wait for a while, and then disconnect (we don't want the disconnect signal to
    # sound immediately after the notes have been played)
    await asyncio.sleep(30)
    if client.is_connected() and not client.is_playing():
        await client.disconnect()


# Serves raw audio packets in 16-bit 48KHz stereo PCM.
# Reference: the data sub-chunk spec in https://archive.is/7pUpZ#selection-160.0-160.1
class NotePlayer(discord.AudioSource):
    SAMPLE_RATE = 48_000

    def __init__(self, notes):
        # List of notes to play.
        self.notes = notes

        # The index of the currently playing note.
        self.n = 0

        # How many packets we have already sent for the current note.
        self.i = 0

    def read(self):
        if self.i >= 48_000:
            self.i = 0
            self.n += 1
            if self.n >= len(self.notes):
                return bytes()

        frame = bytearray()

        for _ in range(960):
            # The factor 2**13 was selected so that
            #   - each sample fits in a signed 16-bit integer (could've been no larger than 2**15-1)
            #   - lowered a bit to avoid it being maximum volume
            amplitude = round(
                2**13 *
                math.sin(
                    2 * math.pi *
                    note_to_frequency(
                        self.notes[self.n]) / NotePlayer.SAMPLE_RATE
                    * self.i
                )
            )

            # Interpret the amplitude as a signed short (int16), pack it in little-endian,
            # and get the two bytes.
            b1, b2 = struct.pack('<h', amplitude)

            frame.append(b1)  # Left channel first byte
            frame.append(b2)  # Left channel second byte
            frame.append(b1)  # Right channel first byte
            frame.append(b2)  # Right channel second byte

            self.i += 1

        return bytes(frame)

    def is_opus(self):
        return False
