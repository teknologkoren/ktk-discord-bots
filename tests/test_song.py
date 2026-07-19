# Tests for bot/song.py: string cleaning, lookup tables, autocomplete,
# embeds, views, and the /song command callback.
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot.song
from bot.song import Song, clean_string

SONGS = [
    {
        'id': 1,
        'page': 12,
        'name': 'Fjäriln vingad',
        'alt': ['Sjung, fjäriln'],
        'chord': 'F',
        'tones': ['F', 'A', 'C'],
    },
    {
        'id': 2,
        'name': 'Bangerlåten',
        'links': [
            ['Noter', 'http://links.test/noter'],
            ['MIDI (alla)', 'http://links.test/midi'],
            ['Sibelius', 'http://links.test/sibelius'],
            ['Repfiler', 'http://links.test/repfiler'],
            ['Textblad', 'http://links.test/textblad'],
        ],
    },
    {'id': 3, 'page': 2, 'name': 'Aftonsång'},
    {'id': 4, 'page': 100, 'name': 'Zulejma', 'chord': 'D'},
]


@pytest.fixture
def cog(tmp_path, monkeypatch):
    instance_dir = tmp_path / 'instance'
    instance_dir.mkdir()
    (instance_dir / 'songs.json').write_text(
        json.dumps(SONGS, ensure_ascii=False), encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    return Song(MagicMock(name='bot'))


def autocomplete_ctx(value):
    ctx = MagicMock(name='autocomplete_ctx')
    ctx.value = value
    return ctx


def async_iterable(items):
    async def gen():
        for item in items:
            yield item
    return gen()


def make_ctx(history=()):
    ctx = MagicMock(name='ctx')
    ctx.respond = AsyncMock(name='ctx.respond')
    ctx.send_response = AsyncMock(name='ctx.send_response')
    ctx.user.id = 42
    ctx.channel.send = AsyncMock(name='ctx.channel.send')
    ctx.channel.history = MagicMock(return_value=async_iterable(history))
    return ctx


def make_history_message(title):
    embed = MagicMock(name='embed')
    embed.title = title
    message = MagicMock(name='message')
    message.embeds = [embed]
    message.add_reaction = AsyncMock(name='message.add_reaction')
    return message


# --- clean_string ---

def test_clean_string_lowercases():
    assert clean_string('HELLO World') == 'hello world'


def test_clean_string_normalizes_unicode():
    assert clean_string('Fjäriln') == 'fjariln'
    assert clean_string('Sjöng épée') == 'sjong epee'


def test_clean_string_removes_punctuation():
    assert clean_string("12. Sjung, fjäriln!") == '12 sjung fjariln'


def test_clean_string_collapses_and_strips_whitespace():
    assert clean_string('  a   b\t c  ') == 'a b c'


# --- Song.__init__ lookup tables ---

def test_by_id_maps_every_song(cog):
    assert set(cog.by_id) == {1, 2, 3, 4}
    assert cog.by_id[2]['name'] == 'Bangerlåten'


def test_by_page_only_contains_songs_with_pages(cog):
    assert set(cog.by_page) == {12, 2, 100}
    assert cog.by_page[12]['name'] == 'Fjäriln vingad'


def test_lookup_contains_name_keys(cog):
    assert cog.lookup['Fjäriln vingad']['id'] == 1
    assert cog.lookup['Bangerlåten']['id'] == 2


def test_lookup_contains_page_dot_name_keys(cog):
    assert cog.lookup['12. Fjäriln vingad']['id'] == 1
    assert cog.lookup['2. Aftonsång']['id'] == 3
    assert '2. Bangerlåten' not in cog.lookup


def test_lookup_contains_alt_names(cog):
    assert cog.lookup['Sjung, fjäriln']['id'] == 1


# --- autocomplete_callback ---

async def test_autocomplete_empty_query_returns_pages_numerically_sorted(cog):
    results = await cog.autocomplete_callback(autocomplete_ctx(''))
    assert results == ['2. Aftonsång', '12. Fjäriln vingad', '100. Zulejma']


async def test_autocomplete_prefix_match_uses_clean_string(cog):
    results = await cog.autocomplete_callback(autocomplete_ctx('fjä'))
    assert results == ['Fjäriln vingad']


async def test_autocomplete_matches_alt_names(cog):
    results = await cog.autocomplete_callback(autocomplete_ctx('sjung'))
    assert results == ['Sjung, fjäriln']


async def test_autocomplete_numeric_query_sorts_numerically(cog):
    results = await cog.autocomplete_callback(autocomplete_ctx('1'))
    assert results == ['12. Fjäriln vingad', '100. Zulejma']


async def test_autocomplete_x_returns_songs_without_page(cog):
    results = await cog.autocomplete_callback(autocomplete_ctx('x'))
    assert results == ['Bangerlåten']


# --- create_embed ---

def test_create_embed_title_includes_page(cog):
    embed = cog.create_embed(cog.by_id[1])
    assert embed.title == '12. Fjäriln vingad'


def test_create_embed_title_without_page(cog):
    embed = cog.create_embed(cog.by_id[2])
    assert embed.title == 'Bangerlåten'


def test_create_embed_description_from_alt(cog):
    embed = cog.create_embed(cog.by_id[1])
    assert embed.description == 'Sjung, fjäriln'


def test_create_embed_empty_description_without_alt(cog):
    embed = cog.create_embed(cog.by_id[3])
    assert not embed.description


def test_create_embed_chord_and_tones_fields(cog):
    embed = cog.create_embed(cog.by_id[1])
    fields = {field.name: field.value for field in embed.fields}
    assert fields == {
        'Startackord / tonart': 'F',
        'Starttoner': 'F, A, C',
    }


def test_create_embed_chord_only(cog):
    embed = cog.create_embed(cog.by_id[4])
    assert [field.name for field in embed.fields] == ['Startackord / tonart']


def test_create_embed_no_fields(cog):
    embed = cog.create_embed(cog.by_id[3])
    assert embed.fields == []


# --- create_song_view ---

async def test_view_ta_ton_button(cog):
    view = cog.create_song_view(cog.by_id[1])
    button = view.children[0]
    assert button.custom_id == 'ta-ton-1'
    assert button.label == 'Ta ton'
    assert button.row == 0


async def test_view_rotary_phone_button_when_url_configured(cog):
    view = cog.create_song_view(cog.by_id[3])
    assert [button.custom_id for button in view.children] == \
        ['ta-ton-3', 'call-3']


async def test_view_no_rotary_phone_button_without_url(cog, monkeypatch):
    monkeypatch.setattr(bot.song, 'ROTARY_PHONE_URL', None)
    view = cog.create_song_view(cog.by_id[3])
    assert [button.custom_id for button in view.children] == ['ta-ton-3']


async def test_view_link_buttons_get_emoji_and_row_per_label(cog):
    view = cog.create_song_view(cog.by_id[2])
    links = view.children[2:]

    assert [button.label for button in links] == \
        ['Noter', 'MIDI (alla)', 'Sibelius', 'Repfiler', 'Textblad']
    assert [button.url for button in links] == \
        [link[1] for link in SONGS[1]['links']]
    assert all(button.custom_id is None for button in links)

    noter, midi, sibelius, repfiler, textblad = links
    assert noter.emoji.name == 'pdf' and noter.row == 0
    assert midi.emoji.name == '\N{MUSICAL KEYBOARD}' and midi.row == 1
    assert sibelius.emoji.name == '\N{MULTIPLE MUSICAL NOTES}' \
        and sibelius.row == 0
    assert repfiler.emoji.name == 'drive' and repfiler.row == 0
    assert textblad.emoji is None and textblad.row == 2


# --- the /song command ---

async def test_song_command_not_found(cog):
    ctx = make_ctx()
    await Song.song.callback(cog, ctx, 'finns inte')
    ctx.respond.assert_awaited_once_with(
        'Jag kunde inte hitta sången du letar efter. :(')
    ctx.send_response.assert_not_called()


async def test_song_command_found_sends_embed_and_view(cog, config):
    vote_message = make_history_message('12. Fjäriln vingad')
    no_embed_message = MagicMock(name='plain_message')
    no_embed_message.embeds = []
    ctx = make_ctx(history=[no_embed_message, vote_message])

    await Song.song.callback(cog, ctx, '12. Fjäriln vingad')

    ctx.respond.assert_not_called()
    ctx.send_response.assert_awaited_once()
    kwargs = ctx.send_response.await_args.kwargs
    assert kwargs['embeds'][0].title == '12. Fjäriln vingad'
    assert kwargs['view'].children[0].custom_id == 'ta-ton-1'

    sine = config['DISCORD_SINE_EMOJI_ID']
    isak = config['DISCORD_ISAK_EMOJI_ID']
    assert vote_message.add_reaction.await_args_list == [
        ((f'<:sine:{sine}>',),),
        ((f'<:isak:{isak}>',),),
    ]


async def test_song_command_found_via_alt_name(cog):
    ctx = make_ctx(history=[make_history_message('12. Fjäriln vingad')])
    await Song.song.callback(cog, ctx, 'Sjung, fjäriln')
    kwargs = ctx.send_response.await_args.kwargs
    assert kwargs['embeds'][0].title == '12. Fjäriln vingad'


async def test_song_command_skips_reactions_when_message_not_found(cog):
    other_message = make_history_message('Nåt annat')
    ctx = make_ctx(history=[other_message])
    await Song.song.callback(cog, ctx, 'Bangerlåten')
    ctx.send_response.assert_awaited_once()
    other_message.add_reaction.assert_not_called()
