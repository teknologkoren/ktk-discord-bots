# Tests for the Streque API client (bot/clients/streque.py).
#
# All HTTP traffic is mocked with aioresponses. The base URL and token come
# from the fake instance.config installed by conftest.py.
import aiohttp
import pytest
from aioresponses import aioresponses

from bot.clients import streque

BASE = 'http://streque.test/api/v1'
AUTH_HEADER = 'Bearer test-streque-token'


@pytest.fixture
def mock_http():
    with aioresponses() as m:
        yield m


def sent_headers(mock_http, method, url):
    """The headers of the (single) request recorded for method+url."""
    requests = mock_http.requests[(method, aiohttp.client.URL(url))]
    assert len(requests) == 1
    return requests[0].kwargs['headers']


async def test_get_request_returns_parsed_json(mock_http):
    mock_http.get(f'{BASE}/some/path', payload={'hello': 'world'})

    result = await streque.get_request('/some/path')

    assert result == {'hello': 'world'}


async def test_get_request_sends_bearer_token(mock_http):
    mock_http.get(f'{BASE}/some/path', payload={})

    await streque.get_request('/some/path')

    headers = sent_headers(mock_http, 'GET', f'{BASE}/some/path')
    assert headers['Authorization'] == AUTH_HEADER


async def test_get_request_raises_on_404(mock_http):
    mock_http.get(f'{BASE}/missing', status=404)

    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        await streque.get_request('/missing')
    assert excinfo.value.status == 404


async def test_get_request_raises_on_500(mock_http):
    mock_http.get(f'{BASE}/broken', status=500)

    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        await streque.get_request('/broken')
    assert excinfo.value.status == 500


async def test_post_request_returns_none(mock_http):
    mock_http.post(f'{BASE}/some/action', payload={'ignored': True})

    result = await streque.post_request('/some/action')

    assert result is None


async def test_post_request_sends_bearer_token(mock_http):
    mock_http.post(f'{BASE}/some/action', status=200)

    await streque.post_request('/some/action')

    headers = sent_headers(mock_http, 'POST', f'{BASE}/some/action')
    assert headers['Authorization'] == AUTH_HEADER


async def test_post_request_raises_on_error(mock_http):
    mock_http.post(f'{BASE}/some/action', status=500)

    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        await streque.post_request('/some/action')
    assert excinfo.value.status == 500


async def test_get_user_by_discord(mock_http):
    user = {'id': 7, 'first_name': 'Anna'}
    mock_http.get(f'{BASE}/users/by-discord/123456', payload=user)

    assert await streque.get_user_by_discord(123456) == user


async def test_get_random_quote(mock_http):
    quote = {'id': 3, 'text': 'Sjung!'}
    mock_http.get(f'{BASE}/quotes/random', payload=quote)

    assert await streque.get_random_quote() == quote


async def test_get_quote_by_id(mock_http):
    quote = {'id': 17, 'text': 'Hej'}
    mock_http.get(f'{BASE}/quotes/17', payload=quote)

    assert await streque.get_quote_by_id(17) == quote


async def test_get_latest_quote_returns_first_element(mock_http):
    quotes = [{'id': 99, 'text': 'newest'}, {'id': 98, 'text': 'older'}]
    mock_http.get(f'{BASE}/quotes?order=desc&limit=1', payload=quotes)

    assert await streque.get_latest_quote() == {'id': 99, 'text': 'newest'}


async def test_get_all_quotes(mock_http):
    quotes = [{'id': 1}, {'id': 2}, {'id': 3}]
    mock_http.get(f'{BASE}/quotes', payload=quotes)

    assert await streque.get_all_quotes() == quotes


async def test_get_birthday_users(mock_http):
    users = [{'id': 5, 'first_name': 'Bo'}]
    mock_http.get(f'{BASE}/users/by-birthday/7/19', payload=users)

    assert await streque.get_birthday_users(7, 19) == users


async def test_mark_notification_sent_posts_to_endpoint(mock_http):
    mock_http.post(f'{BASE}/notifications/42/mark_sent', status=200)

    assert await streque.mark_notification_sent(42) is None

    # The mocked endpoint was actually hit.
    key = ('POST', aiohttp.client.URL(f'{BASE}/notifications/42/mark_sent'))
    assert len(mock_http.requests[key]) == 1


async def test_mark_notification_acknowledged_posts_to_endpoint(mock_http):
    mock_http.post(f'{BASE}/notifications/42/mark_acknowledged', status=200)

    assert await streque.mark_notification_acknowledged(42) is None

    key = ('POST', aiohttp.client.URL(f'{BASE}/notifications/42/mark_acknowledged'))
    assert len(mock_http.requests[key]) == 1
