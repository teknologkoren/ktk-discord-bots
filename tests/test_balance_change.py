# Tests for bot/balance_change.py: kr() formatting, VIP add/remove, DM alerts
# and the threshold logic in handle_balance_change().
from unittest.mock import AsyncMock

import bot.balance_change as balance_change
from tests.conftest import make_bot, make_channel, make_dm_user, make_guild, make_member


# --- kr() ---

def test_kr_converts_ore_to_whole_kronor():
    assert balance_change.kr(12345) == "123 kr"


def test_kr_rounds_up_at_50_ore():
    assert balance_change.kr(12350) == "124 kr"


def test_kr_zero():
    assert balance_change.kr(0) == "0 kr"


def test_kr_negative_amount():
    assert balance_change.kr(-2550) == "-26 kr"


# --- add_to_vip / remove_from_vip ---

async def test_add_to_vip_adds_role_and_announces(config):
    member = make_member(member_id=42)
    vip_role = object()
    vip_channel = make_channel()
    guild = make_guild(
        members={42: member},
        channels={config['DISCORD_VIP_CHANNEL_ID']: vip_channel},
        roles={config['DISCORD_VIP_ROLE_ID']: vip_role},
    )
    bot = make_bot(guild=guild)

    await balance_change.add_to_vip(bot, 42)

    member.add_roles.assert_awaited_once_with(vip_role)
    vip_channel.send.assert_awaited_once()
    assert "<@42>" in vip_channel.send.await_args.args[0]


async def test_remove_from_vip_removes_role_and_announces(config):
    member = make_member(member_id=42)
    vip_role = object()
    vip_channel = make_channel()
    guild = make_guild(
        members={42: member},
        channels={config['DISCORD_VIP_CHANNEL_ID']: vip_channel},
        roles={config['DISCORD_VIP_ROLE_ID']: vip_role},
    )
    bot = make_bot(guild=guild)

    await balance_change.remove_from_vip(bot, 42)

    member.remove_roles.assert_awaited_once_with(vip_role)
    vip_channel.send.assert_awaited_once()
    assert "<@42>" in vip_channel.send.await_args.args[0]


# --- send_* DM alerts ---

async def test_send_vip_status_gained_alert_dms_formatted_amount():
    user, dm = make_dm_user(user_id=42)
    bot = make_bot(users={42: user})

    await balance_change.send_vip_status_gained_alert(bot, 42, 123_400)

    dm.send.assert_awaited_once()
    assert "1234 kr" in dm.send.await_args.args[0]


async def test_send_vip_status_lost_alert_dms_formatted_amount():
    user, dm = make_dm_user(user_id=42)
    bot = make_bot(users={42: user})

    await balance_change.send_vip_status_lost_alert(bot, 42, 98_700)

    dm.send.assert_awaited_once()
    assert "987 kr" in dm.send.await_args.args[0]


async def test_send_low_balance_alert_dms_formatted_amount():
    user, dm = make_dm_user(user_id=42)
    bot = make_bot(users={42: user})

    await balance_change.send_low_balance_alert(bot, 42, 5_600)

    dm.send.assert_awaited_once()
    assert "56 kr" in dm.send.await_args.args[0]


async def test_send_negative_balance_alert_dms_positive_amount():
    user, dm = make_dm_user(user_id=42)
    bot = make_bot(users={42: user})

    await balance_change.send_negative_balance_alert(bot, 42, -2_500)

    dm.send.assert_awaited_once()
    message = dm.send.await_args.args[0]
    assert "25 kr" in message
    assert "-25 kr" not in message


# --- handle_balance_change thresholds ---

def patch_handlers(monkeypatch):
    """Replace all side-effecting functions with AsyncMocks and return them."""
    mocks = {}
    for name in ('send_vip_status_gained_alert', 'send_vip_status_lost_alert',
                 'send_low_balance_alert', 'send_negative_balance_alert',
                 'add_to_vip', 'remove_from_vip'):
        mocks[name] = AsyncMock(name=name)
        monkeypatch.setattr(balance_change, name, mocks[name])
    return mocks


def make_change(old, new, discord_user_id=42):
    return {
        'user_id': 7,
        'discord_user_id': discord_user_id,
        'old_balance': old,
        'new_balance': new,
    }


async def test_not_connected_user_triggers_nothing(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(
        bot, make_change(150_000, 0, discord_user_id=None))

    for mock in mocks.values():
        mock.assert_not_awaited()


async def test_vip_gained_sends_alert_and_adds_role(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(50_000, 120_000))

    mocks['send_vip_status_gained_alert'].assert_awaited_once_with(bot, 42, 120_000)
    mocks['add_to_vip'].assert_awaited_once_with(bot, 42)
    mocks['send_vip_status_lost_alert'].assert_not_awaited()
    mocks['remove_from_vip'].assert_not_awaited()
    mocks['send_low_balance_alert'].assert_not_awaited()
    mocks['send_negative_balance_alert'].assert_not_awaited()


async def test_vip_lost_sends_alert_and_removes_role(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(120_000, 90_000))

    mocks['send_vip_status_lost_alert'].assert_awaited_once_with(bot, 42, 90_000)
    mocks['remove_from_vip'].assert_awaited_once_with(bot, 42)
    mocks['send_vip_status_gained_alert'].assert_not_awaited()
    mocks['add_to_vip'].assert_not_awaited()
    mocks['send_low_balance_alert'].assert_not_awaited()
    mocks['send_negative_balance_alert'].assert_not_awaited()


async def test_crossing_zero_sends_negative_alert_not_low_alert(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(15_000, -2_000))

    mocks['send_negative_balance_alert'].assert_awaited_once_with(bot, 42, -2_000)
    mocks['send_low_balance_alert'].assert_not_awaited()


async def test_crossing_low_threshold_sends_low_alert(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(15_000, 5_000))

    mocks['send_low_balance_alert'].assert_awaited_once_with(bot, 42, 5_000)
    mocks['send_negative_balance_alert'].assert_not_awaited()


async def test_vip_lost_and_crossing_zero_sends_both_alerts(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(120_000, -5_000))

    mocks['send_vip_status_lost_alert'].assert_awaited_once_with(bot, 42, -5_000)
    mocks['remove_from_vip'].assert_awaited_once_with(bot, 42)
    mocks['send_negative_balance_alert'].assert_awaited_once_with(bot, 42, -5_000)
    mocks['send_low_balance_alert'].assert_not_awaited()


async def test_no_threshold_crossed_triggers_nothing(monkeypatch):
    mocks = patch_handlers(monkeypatch)
    bot = make_bot()

    await balance_change.handle_balance_change(bot, make_change(50_000, 60_000))

    for mock in mocks.values():
        mock.assert_not_awaited()
