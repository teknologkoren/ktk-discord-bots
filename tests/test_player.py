# Tests for bot/player.py: note frequencies, vote counting, the audio
# sources, and play_note's early exits.
import math
import struct
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.player import (
    FilePlayer,
    SineWavePlayer,
    get_winning_vote,
    note_to_frequency,
    play_note,
)


def make_reaction(emoji_name, count):
    emoji = MagicMock(name='emoji')
    emoji.name = emoji_name
    reaction = MagicMock(name='reaction')
    reaction.emoji = emoji
    reaction.count = count
    return reaction


def make_message(reactions):
    message = MagicMock(name='message')
    message.reactions = list(reactions)
    return message


# --- note_to_frequency ---

def test_note_to_frequency_a_is_440():
    assert note_to_frequency('A') == 440


def test_note_to_frequency_semitone_steps():
    assert note_to_frequency('B') == pytest.approx(440 * 2 ** (2 / 12))
    assert note_to_frequency('C') == pytest.approx(440 * 2 ** (3 / 12))
    assert note_to_frequency('G') == pytest.approx(440 * 2 ** (10 / 12))


def test_note_to_frequency_sharp_raises_one_semitone():
    assert note_to_frequency('A#') == pytest.approx(440 * 2 ** (1 / 12))
    assert note_to_frequency('F#') == pytest.approx(440 * 2 ** (9 / 12))


def test_note_to_frequency_flat_lowers_one_semitone():
    assert note_to_frequency('Ab') == pytest.approx(440 * 2 ** (-1 / 12))
    assert note_to_frequency('Bb') == pytest.approx(440 * 2 ** (1 / 12))


def test_note_to_frequency_enharmonic_equivalents():
    assert note_to_frequency('A#') == pytest.approx(note_to_frequency('Bb'))


# --- get_winning_vote ---

def test_no_reactions_gives_no_winner():
    assert get_winning_vote(make_message([])) is None


def test_unicode_emoji_reactions_are_ignored():
    thumbs_up = MagicMock(name='reaction')
    thumbs_up.emoji = '\N{THUMBS UP SIGN}'
    thumbs_up.count = 5
    assert get_winning_vote(make_message([thumbs_up])) is None


def test_non_vote_custom_emojis_are_ignored():
    message = make_message([
        make_reaction('other', 10),
        make_reaction('isak', 1),
    ])
    assert get_winning_vote(message) == 'isak'


def test_highest_count_wins():
    message = make_message([
        make_reaction('sine', 2),
        make_reaction('isak', 3),
    ])
    assert get_winning_vote(message) == 'isak'


def test_later_lower_count_does_not_overtake():
    message = make_message([
        make_reaction('isak', 4),
        make_reaction('sine', 1),
    ])
    assert get_winning_vote(message) == 'isak'


def test_tie_returns_first_seen_best():
    message = make_message([
        make_reaction('sine', 2),
        make_reaction('isak', 2),
    ])
    assert get_winning_vote(message) == 'sine'


# --- SineWavePlayer ---

def expected_sample_bytes(note, i):
    amplitude = round(
        2**13 * math.sin(
            2 * math.pi * note_to_frequency(note)
            / SineWavePlayer.SAMPLE_RATE * i))
    b1, b2 = struct.pack('<h', amplitude)
    return bytes([b1, b2, b1, b2])


def test_sine_read_returns_960_stereo_16bit_samples():
    player = SineWavePlayer(['A'])
    frame = player.read()
    assert len(frame) == 960 * 4 == 3840


def test_sine_read_starts_with_silence_then_sine_values():
    player = SineWavePlayer(['A'])
    frame = player.read()
    assert frame[0:4] == b'\x00\x00\x00\x00'
    assert frame[4:8] == expected_sample_bytes('A', 1)
    assert frame[8:12] == expected_sample_bytes('A', 2)


def test_sine_read_advances_state():
    player = SineWavePlayer(['A', 'B'])
    player.read()
    assert (player.n, player.i) == (0, 960)


def test_sine_single_note_ends_after_48000_samples():
    player = SineWavePlayer(['A'])
    for _ in range(50):
        assert len(player.read()) == 3840
    assert player.read() == b''


def test_sine_second_note_starts_after_first_finishes():
    player = SineWavePlayer(['A', 'B'])
    for _ in range(50):
        player.read()

    frame = player.read()
    assert player.n == 1
    assert frame[0:4] == b'\x00\x00\x00\x00'
    assert frame[4:8] == expected_sample_bytes('B', 1)

    for _ in range(49):
        assert len(player.read()) == 3840
    assert player.read() == b''


# --- FilePlayer ---

class FakeFFmpegAudio:
    created_paths = []

    def __init__(self, path):
        FakeFFmpegAudio.created_paths.append(path)
        note = path.rsplit('/', 1)[-1].removesuffix('.wav')
        self.frames = [f'{note}-frame-1'.encode(), f'{note}-frame-2'.encode()]

    def read(self):
        if self.frames:
            return self.frames.pop(0)
        return b''


@pytest.fixture
def fake_ffmpeg(monkeypatch):
    FakeFFmpegAudio.created_paths = []
    monkeypatch.setattr(discord, 'FFmpegPCMAudio', FakeFFmpegAudio)
    return FakeFFmpegAudio


def test_file_player_reads_across_notes_and_ends(fake_ffmpeg):
    player = FilePlayer('isak', ['A', 'Bb'])
    frames = [player.read() for _ in range(6)]
    assert frames == [
        b'A-frame-1',
        b'A-frame-2',
        b'Bb-frame-1',  # transitions to the next note within one read()
        b'Bb-frame-2',
        b'',
        b'',
    ]
    assert fake_ffmpeg.created_paths == \
        ['audio/isak/A.wav', 'audio/isak/Bb.wav']


def test_file_player_opens_first_file_lazily(fake_ffmpeg):
    player = FilePlayer('isak', ['C'])
    assert fake_ffmpeg.created_paths == []
    player.read()
    assert fake_ffmpeg.created_paths == ['audio/isak/C.wav']


# --- play_note early exits ---

def make_interaction():
    interaction = MagicMock(name='interaction')
    interaction.response.send_message = AsyncMock(name='send_message')
    return interaction


async def test_play_note_rejects_dms():
    interaction = make_interaction()
    interaction.guild = None
    await play_note(interaction, MagicMock(name='bot'), ['A'])
    interaction.response.send_message.assert_awaited_once_with(
        content='Jag kan tyvärr inte ta ton från DMs, utan bara från '
                'server-kanaler.',
        ephemeral=True)


async def test_play_note_requires_voice_channel():
    interaction = make_interaction()
    interaction.user.voice = None
    await play_note(interaction, MagicMock(name='bot'), ['A'])
    interaction.response.send_message.assert_awaited_once_with(
        content='Gå in i en röstkanal och försök igen, så följer jag efter '
                'dig och tar ton där!',
        ephemeral=True)
