import asyncio
import math
import struct
from functools import cache

import discord

steps_from_A = {
    'A': 0,
    'B': 2,
    'C': 3,
    'D': 5,
    'E': 7,
    'F': 8,
    'G': 10,
}

vote_emojis = ('sine', 'isak')


@cache
def note_to_frequency(note: str):
    offset = steps_from_A[note[0]]
    if len(note) > 1:
        if note[1] == '#':
            offset += 1
        elif note[1] == 'b':
            offset -= 1

    return 440 * (2 ** (offset/12))


def get_winning_vote(message):
    best = []
    count = 0
    for reaction in message.reactions:
        # There are currently no unicode emojis for voting.
        if isinstance(reaction.emoji, str):
            continue

        if reaction.count >= count and reaction.emoji.name in vote_emojis:
            if reaction.count > count:
                best = []
                count = reaction.count
            best.append(reaction.emoji.name)

    if best:
        return best[0]
    else:
        return None


async def play_note(interaction, bot, notes):
    if interaction.guild is None:
        await interaction.response.send_message(
            content="Jag kan tyvärr inte ta ton från DMs, utan bara från server-kanaler.",
            ephemeral=True)
        return

    if interaction.user.voice is None:
        await interaction.response.send_message(
            content="Gå in i en röstkanal och försök igen, så följer jag efter dig och tar ton där!",
            ephemeral=True)
        return

    # If the bot is already in a voice channel, get the client.
    client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    # Check if the bot is in the same channel as the calling user.
    channel = interaction.user.voice.channel
    if client and client.is_connected():
        if client.channel != channel:
            await client.disconnect()
            client = None

    # Connect to the voice channel that the calling user is in.
    if not client or not client.is_connected():
        client = await channel.connect()

        # Wait a short duration to not have the notes start playing directly after
        # the connect sound.
        await asyncio.sleep(0.5)

    # Play the note sequence.
    # We need to fetch the message explicitly to get the reactions.
    message = await interaction.channel.fetch_message(interaction.message.id)
    if get_winning_vote(message) == 'isak':
        client.play(FilePlayer("isak", notes))
    else:
        client.play(SineWavePlayer(notes))

    # Respond to the interaction to let Discord know it was successful.
    await interaction.response.edit_message()

    # Wait for a while, and then disconnect (we don't want the disconnect signal to
    # sound immediately after the notes have been played)
    await asyncio.sleep(30)
    if client.is_connected() and not client.is_playing():
        await client.disconnect()


# Serves raw audio packets in 16-bit 48KHz stereo PCM.
# Reference: the data sub-chunk spec in https://archive.is/7pUpZ#selection-160.0-160.1
class SineWavePlayer(discord.AudioSource):
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
                        self.notes[self.n]) / SineWavePlayer.SAMPLE_RATE
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


class FilePlayer(discord.AudioSource):

    def __init__(self, folder, notes):
        # List of notes to play.
        self.notes = notes

        # The index of the currently playing note.
        self.n = -1

        # The folder in /audio to get the audio files from.
        self.folder = folder

        # The FFmpegPCMAudio player for the current note.
        self.ffmpeg = None

    def next_note(self):
        self.n += 1
        if self.n >= len(self.notes):
            return False

        self.ffmpeg = discord.FFmpegPCMAudio(
            f"audio/{self.folder}/{self.notes[self.n]}.wav")
        return True

    def read(self):
        if self.ffmpeg is None:
            self.next_note()
        frame = self.ffmpeg.read()
        if not frame and self.next_note():
            frame = self.ffmpeg.read()
        return frame
