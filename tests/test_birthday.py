# Tests for bot/birthday.py: congratulate().
from unittest.mock import AsyncMock, MagicMock

import bot.birthday as birthday
import bot.clients.streque as streque_client
from tests.conftest import make_bot, make_channel, make_guild, make_member

ACTIVE_ROLE = MagicMock(name='active_role')


def make_setup(config, monkeypatch, users, members):
    """Wire up the streque client, guild and bot. Returns (bot, channel)."""
    monkeypatch.setattr(
        streque_client, 'get_birthday_users', AsyncMock(return_value=users))
    channel = make_channel()
    guild = make_guild(
        members=members,
        channels={config['DISCORD_BIRTHDAY_CHANNEL_ID']: channel},
        roles={config['DISCORD_ACTIVE_ROLE_ID']: ACTIVE_ROLE},
    )
    return make_bot(guild=guild), channel


async def test_single_active_birthday_user_is_congratulated(config, monkeypatch):
    bot, channel = make_setup(
        config, monkeypatch,
        users=[{'discord_user_id': 42, 'full_name': 'Anna Alto'}],
        members={42: make_member(member_id=42, roles=[ACTIVE_ROLE])},
    )

    await birthday.congratulate(bot)

    channel.send.assert_awaited_once_with(
        "<@42> fyller år idag! Stort grattis! :partying_face:")


async def test_multiple_users_joined_with_och(config, monkeypatch):
    bot, channel = make_setup(
        config, monkeypatch,
        users=[
            {'discord_user_id': 1, 'full_name': 'Anna Alto'},
            {'discord_user_id': 2, 'full_name': 'Bo Bas'},
            {'discord_user_id': 3, 'full_name': 'Tina Tenor'},
        ],
        members={
            mid: make_member(member_id=mid, roles=[ACTIVE_ROLE])
            for mid in (1, 2, 3)
        },
    )

    await birthday.congratulate(bot)

    channel.send.assert_awaited_once_with(
        "<@1>, <@2> och <@3> fyller år idag! Stort grattis! :partying_face:")


async def test_user_without_discord_id_is_skipped(config, monkeypatch):
    bot, channel = make_setup(
        config, monkeypatch,
        users=[
            {'discord_user_id': None, 'full_name': 'Ulla Utanför'},
            {'discord_user_id': 42, 'full_name': 'Anna Alto'},
        ],
        members={42: make_member(member_id=42, roles=[ACTIVE_ROLE])},
    )

    await birthday.congratulate(bot)

    channel.send.assert_awaited_once_with(
        "<@42> fyller år idag! Stort grattis! :partying_face:")


async def test_member_without_active_role_is_skipped(config, monkeypatch):
    bot, channel = make_setup(
        config, monkeypatch,
        users=[
            {'discord_user_id': 5, 'full_name': 'Pelle Passiv'},
            {'discord_user_id': 42, 'full_name': 'Anna Alto'},
        ],
        members={
            5: make_member(member_id=5, roles=[]),
            42: make_member(member_id=42, roles=[ACTIVE_ROLE]),
        },
    )

    await birthday.congratulate(bot)

    channel.send.assert_awaited_once_with(
        "<@42> fyller år idag! Stort grattis! :partying_face:")


async def test_no_birthdays_sends_nothing(config, monkeypatch):
    bot, channel = make_setup(config, monkeypatch, users=[], members={})

    await birthday.congratulate(bot)

    channel.send.assert_not_awaited()
