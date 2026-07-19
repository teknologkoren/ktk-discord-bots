# Tests for the rotary phone client (bot/clients/rotary_phone.py).
#
# HTTP traffic is mocked with aioresponses; the interaction is a MagicMock
# with async response methods.
import re
from unittest.mock import AsyncMock, MagicMock

import pytest
from aioresponses import aioresponses

from bot.clients import rotary_phone

PLAY_URL = re.compile(r'^http://rotary-phone\.test/play\?')


@pytest.fixture
def mock_http():
    with aioresponses() as m:
        yield m


def make_interaction():
    interaction = MagicMock(name='interaction')
    interaction.response.send_message = AsyncMock(name='send_message')
    interaction.response.edit_message = AsyncMock(name='edit_message')
    return interaction


async def test_play_note_requests_notes_joined_by_comma(mock_http):
    mock_http.get(PLAY_URL, payload={'status': 'ok'})
    interaction = make_interaction()

    await rotary_phone.play_note(interaction, ['C', 'E', 'G'])

    # Exactly one request was made, with the notes as a comma-joined param.
    (method, url), requests = next(iter(mock_http.requests.items()))
    assert method == 'GET'
    assert url.host == 'rotary-phone.test'
    assert url.path == '/play'
    assert len(requests) == 1
    assert requests[0].kwargs['params'] == {'notes': 'C,E,G'}


async def test_play_note_http_error_sends_oops_message(mock_http):
    mock_http.get(PLAY_URL, status=500)
    interaction = make_interaction()

    await rotary_phone.play_note(interaction, ['C'])

    interaction.response.send_message.assert_awaited_once_with(
        content="Oops, telefonen gav ett fel tillbaka... "
                "Prata med Anton så kan han lösa problemet.",
        ephemeral=True,
    )
    interaction.response.edit_message.assert_not_awaited()


async def test_play_note_ok_edits_message(mock_http):
    mock_http.get(PLAY_URL, payload={'status': 'ok'})
    interaction = make_interaction()

    await rotary_phone.play_note(interaction, ['C'])

    interaction.response.edit_message.assert_awaited_once_with()
    interaction.response.send_message.assert_not_awaited()


async def test_play_note_busy_sends_upptagen_message(mock_http):
    mock_http.get(PLAY_URL, payload={'status': 'busy'})
    interaction = make_interaction()

    await rotary_phone.play_note(interaction, ['C'])

    interaction.response.send_message.assert_awaited_once_with(
        content="Telefonen är upptagen. Var vänlig försök igen senare.",
        ephemeral=True,
    )
    interaction.response.edit_message.assert_not_awaited()


async def test_play_note_malformed_sends_snett_message(mock_http):
    mock_http.get(PLAY_URL, payload={'status': 'malformed'})
    interaction = make_interaction()

    await rotary_phone.play_note(interaction, ['C'])

    interaction.response.send_message.assert_awaited_once_with(
        content="Oj, något gick lite snett där! "
                "Prata med Anton så kan han lösa problemet.",
        ephemeral=True,
    )
    interaction.response.edit_message.assert_not_awaited()
