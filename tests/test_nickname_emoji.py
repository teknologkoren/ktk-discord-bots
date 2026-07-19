# Tests for bot/nickname_emoji.py: map_emoji, set_emoji, handle_balance_change
# and periodic_update.
from unittest.mock import AsyncMock, MagicMock

from aiohttp.client_exceptions import ClientResponseError

import bot.clients.streque as streque_client
import bot.nickname_emoji as nickname_emoji
from tests.conftest import make_bot, make_guild, make_member


# --- map_emoji ---

def test_map_emoji_replaces_russian_flag_with_skull():
    assert nickname_emoji.map_emoji('🇷🇺') == '💀'


def test_map_emoji_replaces_finnish_flag_with_skull():
    assert nickname_emoji.map_emoji('🇫🇮') == '💀'


def test_map_emoji_passes_through_other_emojis():
    assert nickname_emoji.map_emoji('🍺') == '🍺'


def test_map_emoji_passes_through_none():
    assert nickname_emoji.map_emoji(None) is None


# --- set_emoji ---

async def test_set_emoji_adds_emoji_to_bare_nick():
    member = make_member(display_name='Anna')

    await nickname_emoji.set_emoji(member, '🍺')

    member.edit.assert_awaited_once()
    assert member.edit.await_args.kwargs['nick'] == '🍺Anna'


async def test_set_emoji_removes_emoji_when_new_is_none():
    member = make_member(display_name='🍺Anna')

    await nickname_emoji.set_emoji(member, None)

    member.edit.assert_awaited_once()
    assert member.edit.await_args.kwargs['nick'] == 'Anna'


async def test_set_emoji_switches_to_new_emoji():
    member = make_member(display_name='🍺Anna')

    await nickname_emoji.set_emoji(member, '💀')

    member.edit.assert_awaited_once()
    assert member.edit.await_args.kwargs['nick'] == '💀Anna'


async def test_set_emoji_noop_when_same_emoji():
    member = make_member(display_name='🍺Anna')

    await nickname_emoji.set_emoji(member, '🍺')

    member.edit.assert_not_awaited()


async def test_set_emoji_noop_when_no_emoji_and_none():
    member = make_member(display_name='Anna')

    await nickname_emoji.set_emoji(member, None)

    member.edit.assert_not_awaited()


async def test_set_emoji_maps_flag_before_applying():
    member = make_member(display_name='Anna')

    await nickname_emoji.set_emoji(member, '🇷🇺')

    member.edit.assert_awaited_once()
    assert member.edit.await_args.kwargs['nick'] == '💀Anna'


# --- handle_balance_change ---

async def test_handle_balance_change_sets_emoji_on_member():
    member = make_member(member_id=42, display_name='Anna')
    guild = make_guild(members={42: member})
    bot = make_bot(guild=guild)

    await nickname_emoji.handle_balance_change(
        bot, {'discord_user_id': 42, 'new_emoji': '🍻'})

    guild.fetch_member.assert_awaited_once_with(42)
    member.edit.assert_awaited_once()
    assert member.edit.await_args.kwargs['nick'] == '🍻Anna'


# --- periodic_update ---

def make_members_guild(members):
    """A guild whose fetch_members() yields the given members."""
    guild = make_guild()

    async def gen():
        for member in members:
            yield member

    guild.fetch_members = MagicMock(side_effect=lambda: gen())
    return guild


async def test_periodic_update_syncs_member_with_managed_emoji(monkeypatch):
    no_nick = make_member(member_id=1, display_name='Nolle', nick=None)
    plain_nick = make_member(member_id=2, display_name='Bo', nick='Bo')
    emoji_nick = make_member(member_id=3, display_name='🍺Anna', nick='🍺Anna')
    guild = make_members_guild([no_nick, plain_nick, emoji_nick])
    bot = make_bot(guild=guild)

    get_user = AsyncMock(return_value={'bac_emoji': '💀'})
    monkeypatch.setattr(streque_client, 'get_user_by_discord', get_user)

    await nickname_emoji.periodic_update(bot)

    get_user.assert_awaited_once_with(3)
    emoji_nick.edit.assert_awaited_once()
    assert emoji_nick.edit.await_args.kwargs['nick'] == '💀Anna'
    no_nick.edit.assert_not_awaited()
    plain_nick.edit.assert_not_awaited()


async def test_periodic_update_handles_404_for_unconnected_member(monkeypatch):
    member = make_member(member_id=3, display_name='🍺Anna', nick='🍺Anna')
    guild = make_members_guild([member])
    bot = make_bot(guild=guild)

    error = ClientResponseError(request_info=None, history=None, status=404)
    monkeypatch.setattr(
        streque_client, 'get_user_by_discord', AsyncMock(side_effect=error))

    # Must not raise.
    await nickname_emoji.periodic_update(bot)

    member.edit.assert_not_awaited()


async def test_periodic_update_swallows_other_client_errors(monkeypatch):
    member = make_member(member_id=3, display_name='🍺Anna', nick='🍺Anna')
    guild = make_members_guild([member])
    bot = make_bot(guild=guild)

    error = ClientResponseError(request_info=None, history=None, status=500)
    monkeypatch.setattr(
        streque_client, 'get_user_by_discord', AsyncMock(side_effect=error))

    # Must not raise.
    await nickname_emoji.periodic_update(bot)

    member.edit.assert_not_awaited()
