# Shared test fixtures and configuration.
#
# The bot modules read their configuration with `from instance.config import ...`
# at import time, and `instance/` only exists on deployed machines (it is
# gitignored). To make the modules importable in tests, we register fake
# `instance.config` and `instance.group_config` modules in `sys.modules`
# *before* any bot module is imported.
#
# Note that since the bot modules import config values with
# `from instance.config import X`, they hold their own reference to each value.
# Tests that need a different value must monkeypatch the attribute on the bot
# module itself, e.g. `monkeypatch.setattr(bot.song, "ROTARY_PHONE_URL", None)`.
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

TEST_CONFIG = {
    'STREQUE_BASE_URL': 'http://streque.test',
    'STREQUE_URL': 'http://streque.test/api/v1',
    'STREQUE_TOKEN': 'test-streque-token',

    'STREQUE_BOT_TOKEN': 'test-streque-bot-token',
    'CHOIR_BOT_TOKEN': None,

    'DISCORD_GUILD_ID': 1000,
    'DISCORD_VIP_ROLE_ID': 1001,
    'DISCORD_VIP_CHANNEL_ID': 1002,
    'DISCORD_BIRTHDAY_CHANNEL_ID': 1003,
    'DISCORD_ACTIVE_ROLE_ID': 1004,
    'DISCORD_VECKOMEJL_CHANNEL_ID': 1005,
    'DISCORD_CLUB_CATEGORY_ID': 1006,
    'DISCORD_SINE_EMOJI_ID': 1007,
    'DISCORD_ISAK_EMOJI_ID': 1008,
    'CARL_REACTION_ROLE_MESSAGE_ID': 1009,
    'CARL_REACTION_ROLE_CHANNEL_ID': 1010,

    'VECKOMEJL_FOLDER_ID': 'veckomejl-folder-id',
    'VECKOMEJL_MAILING_LIST': 'aktiva@lists.example.com',
    'GMAIL_LABEL_SENT_TO_DISCORD': 'test-label-id',

    'DRIVE_SHEET_MUSIC_FOLDER': None,
    'DRIVE_MIDI_FULL_FOLDER': None,
    'DRIVE_MIDI_PARTS_FOLDER': None,
    'DRIVE_SIBELIUS_FOLDER': None,

    'ROTARY_PHONE_URL': 'http://rotary-phone.test/play',

    'BOARD_VECKOMEJL_LINK': 'https://docs.example.com/veckomejl',
    'DISCORD_BOARD_GUILD_ID': 2000,
    'DISCORD_BOARD_VECKOMEJL_CHANNEL_ID': 2001,

    'POTATO_BOT_TOKEN': None,
    'DISCORD_POTATO_CHANNEL': 1011,
}

TEST_ROLES = {
    3001: ['Anna Alto', 'Bo Bas'],
    3002: ['Bo Bas', 'Tina Tenor'],
}


def _install_fake_instance_modules():
    config = types.ModuleType('instance.config')
    for key, value in TEST_CONFIG.items():
        setattr(config, key, value)
    sys.modules['instance.config'] = config

    group_config = types.ModuleType('instance.group_config')
    group_config.ROLES = TEST_ROLES
    sys.modules['instance.group_config'] = group_config


_install_fake_instance_modules()


@pytest.fixture
def config():
    """The fake config values, for asserting against IDs etc."""
    return dict(TEST_CONFIG)


def make_channel():
    """A text channel that records messages sent to it."""
    channel = MagicMock(name='channel')
    channel.send = AsyncMock(name='channel.send')
    return channel


def make_member(member_id=42, display_name='Test User', roles=(), nick=None):
    member = MagicMock(name='member')
    member.id = member_id
    member.display_name = display_name
    member.nick = nick
    member.roles = list(roles)
    member.add_roles = AsyncMock(name='member.add_roles')
    member.remove_roles = AsyncMock(name='member.remove_roles')
    member.edit = AsyncMock(name='member.edit')
    return member


def make_guild(members=None, channels=None, roles=None):
    """A guild whose fetch_member/fetch_channel/get_role look things up in
    the given id -> object dicts."""
    members = members or {}
    channels = channels or {}
    roles = roles or {}

    guild = MagicMock(name='guild')
    guild.fetch_member = AsyncMock(side_effect=lambda mid: members[mid])
    guild.fetch_channel = AsyncMock(side_effect=lambda cid: channels[cid])
    guild.get_role = MagicMock(side_effect=lambda rid: roles.get(rid))
    return guild


def make_bot(guild=None, users=None):
    """A bot whose fetch_guild returns `guild` and whose fetch_user looks up
    in the id -> user dict."""
    users = users or {}

    bot = MagicMock(name='bot')
    bot.fetch_guild = AsyncMock(return_value=guild)
    bot.fetch_user = AsyncMock(side_effect=lambda uid: users[uid])
    return bot


def make_dm_user(user_id=42):
    """A user with a DM channel that records messages. Returns (user, dm)."""
    dm = make_channel()
    user = MagicMock(name='user')
    user.id = user_id
    user.create_dm = AsyncMock(return_value=dm)
    return user, dm
