# Tests for bot/veckomejl.py: notify_if_veckomejl, check_for_email and
# board_reminder.
from unittest.mock import AsyncMock, MagicMock

import bot.veckomejl as veckomejl
from tests.conftest import make_bot, make_channel, make_guild

DOC_MIME = 'application/vnd.google-apps.document'


def make_google_client(files=None, email=None):
    client = MagicMock(name='google_client')
    client.list_drive_folder = AsyncMock(return_value={'files': files or []})
    client.get_new_email = AsyncMock(return_value=email)
    return client


def make_veckomejl_bot(config):
    channel = make_channel()
    guild = make_guild(channels={config['DISCORD_VECKOMEJL_CHANNEL_ID']: channel})
    return make_bot(guild=guild), channel


def pick_first_message(monkeypatch):
    monkeypatch.setattr(veckomejl.random, 'choice', lambda seq: seq[0])


# --- notify_if_veckomejl ---

async def test_subject_without_veckomejl_returns_false(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client()

    result = await veckomejl.notify_if_veckomejl(bot, google_client, 'Kallelse till årsmöte')

    assert result is False
    google_client.list_drive_folder.assert_not_awaited()
    channel.send.assert_not_awaited()


async def test_subject_without_week_number_returns_false(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client()

    result = await veckomejl.notify_if_veckomejl(bot, google_client, 'Veckomejl')

    assert result is False
    channel.send.assert_not_awaited()


async def test_matching_drive_doc_gets_link_button(config, monkeypatch):
    pick_first_message(monkeypatch)
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(files=[
        # Wrong mime type, must be skipped even though the number matches.
        {'name': 'Veckomejl 4', 'mimeType': 'image/png',
         'webViewLink': 'http://drive.test/image'},
        # Wrong week number.
        {'name': 'Veckomejl 3', 'mimeType': DOC_MIME,
         'webViewLink': 'http://drive.test/doc3'},
        # The right document.
        {'name': 'Veckomejl 4', 'mimeType': DOC_MIME,
         'webViewLink': 'http://drive.test/doc4'},
    ])

    result = await veckomejl.notify_if_veckomejl(
        bot, google_client, '[KTK] Veckomejl v4')

    assert result is True
    channel.send.assert_awaited_once()
    message = channel.send.await_args.args[0]
    view = channel.send.await_args.kwargs['view']
    assert message == veckomejl.VECKOMEJL_MESSAGES[0]
    assert view is not None
    button = view.children[0]
    assert button.url == 'http://drive.test/doc4'
    assert button.label == 'Veckomejl v4'


async def test_week_40_doc_does_not_match_week_4(config, monkeypatch):
    pick_first_message(monkeypatch)
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(files=[
        {'name': 'Veckomejl 40', 'mimeType': DOC_MIME,
         'webViewLink': 'http://drive.test/doc40'},
    ])

    result = await veckomejl.notify_if_veckomejl(bot, google_client, 'Veckomejl v4')

    assert result is True
    channel.send.assert_awaited_once()
    assert channel.send.await_args.kwargs['view'] is None
    assert '**Veckomejl v4**' in channel.send.await_args.args[0]


async def test_no_matching_doc_puts_subject_in_message(config, monkeypatch):
    pick_first_message(monkeypatch)
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(files=[])

    result = await veckomejl.notify_if_veckomejl(bot, google_client, 'Veckomejl v12')

    assert result is True
    message = channel.send.await_args.args[0]
    assert message == veckomejl.VECKOMEJL_MESSAGES[0] + '**Veckomejl v12**'


async def test_override_week_uses_override_text(config, monkeypatch):
    pick_first_message(monkeypatch)
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(files=[])

    result = await veckomejl.notify_if_veckomejl(bot, google_client, 'Veckomejl v45')

    assert result is True
    message = channel.send.await_args.args[0]
    assert message.startswith(veckomejl.VECKOMEJL_OVERRIDES['45'])
    assert '**Veckomejl v45**' in message


# --- check_for_email ---

async def test_no_new_email_does_nothing(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(email=None)

    await veckomejl.check_for_email(bot, google_client)

    bot.fetch_guild.assert_not_awaited()
    channel.send.assert_not_awaited()


async def test_email_to_other_mailing_list_does_nothing(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(email={
        'mailing_list': 'annan-lista@lists.example.com',
        'subject': 'Veckomejl v12',
        'sender': 'Ordförande',
    })

    await veckomejl.check_for_email(bot, google_client)

    channel.send.assert_not_awaited()


async def test_email_without_mailing_list_does_nothing(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(email={
        'mailing_list': None,
        'subject': 'Veckomejl v12',
        'sender': 'Ordförande',
    })

    await veckomejl.check_for_email(bot, google_client)

    channel.send.assert_not_awaited()


async def test_veckomejl_email_takes_notify_path(config, monkeypatch):
    pick_first_message(monkeypatch)
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(email={
        'mailing_list': 'aktiva@lists.example.com',
        'subject': 'Veckomejl v12',
        'sender': 'Ordförande',
    })

    await veckomejl.check_for_email(bot, google_client)

    channel.send.assert_awaited_once()
    message = channel.send.await_args.args[0]
    assert '**Veckomejl v12**' in message
    assert 'Nytt mejl till aktiva' not in message


async def test_other_email_to_list_sends_fallback_notification(config):
    bot, channel = make_veckomejl_bot(config)
    google_client = make_google_client(email={
        'mailing_list': 'aktiva@lists.example.com',
        'subject': 'Kallelse till årsmöte',
        'sender': 'Sekreteraren',
    })

    await veckomejl.check_for_email(bot, google_client)

    channel.send.assert_awaited_once_with(
        'Nytt mejl till aktiva: **Kallelse till årsmöte** från *Sekreteraren*')


# --- board_reminder ---

async def test_board_reminder_sends_with_link_button(config):
    channel = make_channel()
    guild = make_guild(
        channels={config['DISCORD_BOARD_VECKOMEJL_CHANNEL_ID']: channel})
    bot = make_bot(guild=guild)

    await veckomejl.board_reminder(bot)

    bot.fetch_guild.assert_awaited_once_with(config['DISCORD_BOARD_GUILD_ID'])
    channel.send.assert_awaited_once()
    assert 'Sista chansen' in channel.send.await_args.args[0]
    view = channel.send.await_args.kwargs['view']
    assert view.children[0].url == config['BOARD_VECKOMEJL_LINK']


async def test_board_reminder_without_link_sends_no_view(config, monkeypatch):
    monkeypatch.setattr(veckomejl, 'BOARD_VECKOMEJL_LINK', None)
    channel = make_channel()
    guild = make_guild(
        channels={config['DISCORD_BOARD_VECKOMEJL_CHANNEL_ID']: channel})
    bot = make_bot(guild=guild)

    await veckomejl.board_reminder(bot)

    channel.send.assert_awaited_once()
    assert channel.send.await_args.kwargs['view'] is None
