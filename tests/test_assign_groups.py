# Tests for bot/assign_groups.py: set_extra_roles().
from unittest.mock import AsyncMock, MagicMock

import bot.assign_groups as assign_groups
import bot.clients.streque as streque_client
from tests.conftest import make_bot, make_channel, make_guild, make_member


def make_setup(config, monkeypatch, full_name, balance):
    """A member in a guild with the group and VIP roles. Returns
    (member, roles-by-id, vip_channel)."""
    monkeypatch.setattr(
        streque_client, 'get_user_by_discord',
        AsyncMock(return_value={'full_name': full_name, 'balance': balance}))

    roles = {
        3001: MagicMock(name='role_3001'),
        3002: MagicMock(name='role_3002'),
        config['DISCORD_VIP_ROLE_ID']: MagicMock(name='vip_role'),
    }
    vip_channel = make_channel()
    guild = make_guild(
        channels={config['DISCORD_VIP_CHANNEL_ID']: vip_channel},
        roles=roles,
    )
    member = make_member(member_id=42, display_name=full_name)
    member.guild = guild
    return member, roles, vip_channel


async def test_user_in_one_group_gets_that_role(config, monkeypatch):
    member, roles, vip_channel = make_setup(
        config, monkeypatch, 'Anna Alto', balance=0)

    await assign_groups.set_extra_roles(member, make_bot())

    member.add_roles.assert_awaited_once_with(roles[3001])
    vip_channel.send.assert_not_awaited()


async def test_user_in_two_groups_gets_both_roles(config, monkeypatch):
    member, roles, vip_channel = make_setup(
        config, monkeypatch, 'Bo Bas', balance=0)

    await assign_groups.set_extra_roles(member, make_bot())

    member.add_roles.assert_awaited_once_with(roles[3001], roles[3002])
    vip_channel.send.assert_not_awaited()


async def test_high_balance_adds_vip_role_and_welcomes(config, monkeypatch):
    member, roles, vip_channel = make_setup(
        config, monkeypatch, 'Tina Tenor', balance=150_000)

    await assign_groups.set_extra_roles(member, make_bot())

    member.add_roles.assert_awaited_once_with(
        roles[3002], roles[config['DISCORD_VIP_ROLE_ID']])
    vip_channel.send.assert_awaited_once()
    assert '<@42>' in vip_channel.send.await_args.args[0]


async def test_low_balance_gives_no_vip_role(config, monkeypatch):
    member, roles, vip_channel = make_setup(
        config, monkeypatch, 'Tina Tenor', balance=99_999)

    await assign_groups.set_extra_roles(member, make_bot())

    member.add_roles.assert_awaited_once_with(roles[3002])
    vip_channel.send.assert_not_awaited()


async def test_unknown_name_and_low_balance_adds_no_roles(config, monkeypatch):
    member, roles, vip_channel = make_setup(
        config, monkeypatch, 'Okänd Person', balance=0)

    await assign_groups.set_extra_roles(member, make_bot())

    member.add_roles.assert_awaited_once_with()
    vip_channel.send.assert_not_awaited()
