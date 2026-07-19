# Tests for bot/notifications.py: create_notification_view, handle_notification
# and mark_read_callback.
#
# Note: discord.ui.View requires a running event loop, so even the pure view
# construction tests are async.
from unittest.mock import AsyncMock, MagicMock

import discord

import bot.clients.streque as streque_client
import bot.notifications as notifications
from tests.conftest import make_bot, make_dm_user


# --- create_notification_view ---

async def test_view_has_mark_read_and_link_buttons():
    view = notifications.create_notification_view(17)

    assert len(view.children) == 2
    mark_read, link = view.children
    assert mark_read.custom_id == 'notification-17'
    assert mark_read.style == discord.ButtonStyle.primary
    assert mark_read.disabled is False
    assert link.url == 'https://www.streque.se/notifications'
    assert link.custom_id is None


async def test_view_disabled_flag_propagates_to_mark_read_button():
    view = notifications.create_notification_view(17, button_disabled=True)

    mark_read, link = view.children
    assert mark_read.disabled is True
    assert link.disabled is False


# --- handle_notification ---

async def test_unconnected_user_gets_no_dm(monkeypatch):
    mark_sent = AsyncMock()
    monkeypatch.setattr(streque_client, 'mark_notification_sent', mark_sent)
    bot = make_bot()

    await notifications.handle_notification(bot, {
        'notification_id': 5,
        'user_id': 7,
        'discord_user_id': None,
        'text': 'Hej!',
    })

    bot.fetch_user.assert_not_awaited()
    mark_sent.assert_not_awaited()


async def test_connected_user_gets_dm_and_notification_marked_sent(monkeypatch):
    mark_sent = AsyncMock()
    monkeypatch.setattr(streque_client, 'mark_notification_sent', mark_sent)
    user, dm = make_dm_user(user_id=42)
    bot = make_bot(users={42: user})

    await notifications.handle_notification(bot, {
        'notification_id': 5,
        'user_id': 7,
        'discord_user_id': 42,
        'text': 'Du har fått en ny notis!',
    })

    dm.send.assert_awaited_once()
    assert dm.send.await_args.args[0] == 'Du har fått en ny notis!'
    view = dm.send.await_args.kwargs['view']
    assert view.children[0].custom_id == 'notification-5'
    mark_sent.assert_awaited_once_with(5)


# --- mark_read_callback ---

async def test_mark_read_callback_acknowledges_and_disables_button(monkeypatch):
    mark_acknowledged = AsyncMock()
    monkeypatch.setattr(
        streque_client, 'mark_notification_acknowledged', mark_acknowledged)

    interaction = MagicMock(name='interaction')
    interaction.custom_id = 'notification-99'
    interaction.response.edit_message = AsyncMock()

    await notifications.mark_read_callback(interaction)

    mark_acknowledged.assert_awaited_once_with('99')
    interaction.response.edit_message.assert_awaited_once()
    view = interaction.response.edit_message.await_args.kwargs['view']
    assert view.children[0].custom_id == 'notification-99'
    assert view.children[0].disabled is True
