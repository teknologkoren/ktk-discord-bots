# Tests for bot/potato.py: the advent calendar date gating in post().
import datetime

import bot.potato as potato
from tests.conftest import make_bot, make_channel, make_guild


class FakeDateTime:
    """Stub for the module's `datetime` name, with a fixed now()."""
    fixed_now = None

    @classmethod
    def now(cls):
        return cls.fixed_now


def freeze_date(monkeypatch, year, month, day):
    FakeDateTime.fixed_now = datetime.datetime(year, month, day, 12, 0)
    monkeypatch.setattr(potato, 'datetime', FakeDateTime)


def make_potato_bot(config):
    channel = make_channel()
    guild = make_guild(channels={config['DISCORD_POTATO_CHANNEL']: channel})
    return make_bot(guild=guild), channel


async def test_no_post_outside_december(config, monkeypatch):
    freeze_date(monkeypatch, 2026, 11, 5)
    bot, channel = make_potato_bot(config)

    await potato.post(bot)

    bot.fetch_guild.assert_not_awaited()
    channel.send.assert_not_awaited()


async def test_no_post_after_december_24(config, monkeypatch):
    freeze_date(monkeypatch, 2026, 12, 25)
    bot, channel = make_potato_bot(config)

    await potato.post(bot)

    bot.fetch_guild.assert_not_awaited()
    channel.send.assert_not_awaited()


async def test_posts_video_on_advent_day(config, monkeypatch):
    freeze_date(monkeypatch, 2026, 12, 12)
    bot, channel = make_potato_bot(config)

    await potato.post(bot)

    channel.send.assert_awaited_once()
    message = channel.send.await_args.args[0]
    url, title = potato.videos[12]
    assert 'Lucka 12' in message
    assert title in message
    assert url in message


async def test_posts_video_on_december_1_and_24(config, monkeypatch):
    for day in (1, 24):
        freeze_date(monkeypatch, 2026, 12, day)
        bot, channel = make_potato_bot(config)

        await potato.post(bot)

        channel.send.assert_awaited_once()
        message = channel.send.await_args.args[0]
        url, title = potato.videos[day]
        assert f'Lucka {day}' in message
        assert title in message
        assert url in message
