# Tests for bot/quote.py: embed contents, the permalink pattern, and the
# /quote subcommand callbacks (with the Streque client monkeypatched).
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot.quote
from bot.clients import streque
from bot.quote import Quote

QUOTE = {
    'id': 1971,
    'text': 'Nu tar vi en Streque!',
    'who': 'Anna Alto',
    'timestamp': 1600000000,
}

OTHER_QUOTE = {
    'id': 7,
    'text': 'God afton.',
    'who': 'Bo Bas',
    'timestamp': 1500000000,
}


@pytest.fixture
def cog():
    return Quote(MagicMock(name='bot'))


def make_ctx():
    ctx = MagicMock(name='ctx')
    ctx.respond = AsyncMock(name='ctx.respond')
    return ctx


def responded_embed(ctx):
    embeds = ctx.respond.await_args.kwargs['embeds']
    assert len(embeds) == 1
    return embeds[0]


# --- create_embed ---

def test_create_embed_contents(cog):
    embed = cog.create_embed(QUOTE)
    assert embed.title == 'Citat #1971'
    assert embed.url == 'https://www.streque.se/quotes/#quote-1971'
    assert embed.description == 'Nu tar vi en Streque!'
    assert embed.timestamp.timestamp() == 1600000000
    assert len(embed.fields) == 1
    assert embed.fields[0].name == '– Anna Alto'


# --- quote_id_pattern ---

def test_quote_id_pattern_extracts_id_from_permalink():
    match = Quote.quote_id_pattern.search(
        'https://www.streque.se/quotes/#quote-1971')
    assert match.group(1) == '1971'


def test_quote_id_pattern_rejects_other_urls():
    assert Quote.quote_id_pattern.search('https://www.streque.se/') is None
    assert Quote.quote_id_pattern.search('#quote-') is None


# --- /quote id ---

async def test_id_responds_with_embed(cog, monkeypatch):
    get_quote = AsyncMock(return_value=QUOTE)
    monkeypatch.setattr(streque, 'get_quote_by_id', get_quote)
    ctx = make_ctx()

    await Quote.id.callback(cog, ctx, 1971)

    get_quote.assert_awaited_once_with(1971)
    assert responded_embed(ctx).title == 'Citat #1971'


async def test_id_reports_failure(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_quote_by_id', AsyncMock(side_effect=RuntimeError))
    ctx = make_ctx()

    await Quote.id.callback(cog, ctx, 1971)

    ctx.respond.assert_awaited_once_with(
        "I couldn't find the quote you were looking for...")


# --- /quote roulette ---

async def test_roulette_responds_with_embed(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_random_quote', AsyncMock(return_value=OTHER_QUOTE))
    ctx = make_ctx()

    await Quote.roulette.callback(cog, ctx)

    assert responded_embed(ctx).title == 'Citat #7'


async def test_roulette_reports_failure(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_random_quote', AsyncMock(side_effect=RuntimeError))
    ctx = make_ctx()

    await Quote.roulette.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "I didn't manage to get a random quote. Please inform the webmaster "
        "so they can fix me."
    )


# --- /quote latest ---

async def test_latest_responds_with_embed(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_latest_quote', AsyncMock(return_value=QUOTE))
    ctx = make_ctx()

    await Quote.latest.callback(cog, ctx)

    assert responded_embed(ctx).title == 'Citat #1971'


async def test_latest_reports_failure(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_latest_quote', AsyncMock(side_effect=RuntimeError))
    ctx = make_ctx()

    await Quote.latest.callback(cog, ctx)

    ctx.respond.assert_awaited_once_with(
        "I didn't manage to fetch the latest quote. Please inform the "
        "webmaster so they can fix me."
    )


# --- /quote url ---

async def test_url_extracts_id_from_permalink(cog, monkeypatch):
    get_quote = AsyncMock(return_value=QUOTE)
    monkeypatch.setattr(streque, 'get_quote_by_id', get_quote)
    ctx = make_ctx()

    await Quote.url.callback(
        cog, ctx, 'https://www.streque.se/quotes/#quote-1971')

    get_quote.assert_awaited_once_with(1971)
    assert responded_embed(ctx).title == 'Citat #1971'


async def test_url_reports_lookup_failure(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_quote_by_id', AsyncMock(side_effect=RuntimeError))
    ctx = make_ctx()

    await Quote.url.callback(
        cog, ctx, 'https://www.streque.se/quotes/#quote-9999')

    ctx.respond.assert_awaited_once_with(
        "I couldn't find the quote you were looking for...")


# --- /quote search ---

async def test_search_matches_text_case_insensitively(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_all_quotes',
        AsyncMock(return_value=[QUOTE, OTHER_QUOTE]))
    monkeypatch.setattr(bot.quote.random, 'choice', lambda seq: seq[0])
    ctx = make_ctx()

    await Quote.search.callback(cog, ctx, 'STREQUE!')

    assert ctx.respond.await_args.args == ('Sökte efter: *STREQUE!*',)
    assert responded_embed(ctx).title == 'Citat #1971'


async def test_search_matches_who_case_insensitively(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_all_quotes',
        AsyncMock(return_value=[QUOTE, OTHER_QUOTE]))
    monkeypatch.setattr(bot.quote.random, 'choice', lambda seq: seq[0])
    ctx = make_ctx()

    await Quote.search.callback(cog, ctx, 'bo bas')

    assert responded_embed(ctx).title == 'Citat #7'


async def test_search_picks_among_all_matches(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_all_quotes',
        AsyncMock(return_value=[QUOTE, OTHER_QUOTE]))
    seen = []
    monkeypatch.setattr(
        bot.quote.random, 'choice',
        lambda seq: seen.extend(seq) or seq[-1])
    ctx = make_ctx()

    # Both quotes contain an "a" in their text/who.
    await Quote.search.callback(cog, ctx, 'a')

    assert seen == [QUOTE, OTHER_QUOTE]
    assert responded_embed(ctx).title == 'Citat #7'


async def test_search_no_match(cog, monkeypatch):
    monkeypatch.setattr(
        streque, 'get_all_quotes',
        AsyncMock(return_value=[QUOTE, OTHER_QUOTE]))
    ctx = make_ctx()

    await Quote.search.callback(cog, ctx, 'zzz finns inte')

    ctx.respond.assert_awaited_once_with(
        "I couldn't find any quotes matching your query.")
