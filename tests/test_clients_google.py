# Tests for the Google API client (bot/clients/google.py).
#
# The client reads its OAuth credentials from 'instance/token.json' relative
# to the working directory, so tests chdir into a tmp_path with a fake token
# file. Aiogoogle itself is replaced by a small fake async context manager;
# the gmail/drive service objects are MagicMocks whose method calls return
# sentinel request objects that the fake `as_user` maps to canned responses.
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot.clients.google as google_client
from bot.clients.google import GoogleAPIClient

TOKEN_JSON = {
    'client_id': 'test-client-id',
    'client_secret': 'test-client-secret',
    'scopes': ['scope-a', 'scope-b'],
    'token': 'test-access-token',
    'refresh_token': 'test-refresh-token',
    'token_uri': 'https://oauth.test/token',
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A GoogleAPIClient constructed from a fake instance/token.json."""
    (tmp_path / 'instance').mkdir()
    (tmp_path / 'instance' / 'token.json').write_text(json.dumps(TOKEN_JSON))
    monkeypatch.chdir(tmp_path)
    return GoogleAPIClient()


@pytest.fixture
def fake_aiogoogle(monkeypatch):
    """Replace Aiogoogle with a fake async context manager whose `as_user`
    looks up responses in `FakeAiogoogle.responses`, keyed by the sentinel
    request objects that the MagicMock services return."""

    class FakeAiogoogle:
        responses = {}
        as_user_calls = []

        def __init__(self, user_creds=None, client_creds=None):
            self.user_creds = user_creds
            self.client_creds = client_creds
            self.oauth2 = MagicMock(name='oauth2')
            self.oauth2.refresh = AsyncMock(return_value=(False, user_creds))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def as_user(self, request, raise_for_status=True):
            FakeAiogoogle.as_user_calls.append(request)
            return FakeAiogoogle.responses[request]

    monkeypatch.setattr(google_client, 'Aiogoogle', FakeAiogoogle)
    return FakeAiogoogle


def stub_services(client):
    """Give the client MagicMock gmail/drive services so that initialize()
    skips service discovery."""
    client.gmail = MagicMock(name='gmail')
    client.drive = MagicMock(name='drive')


def test_init_parses_token_file(client):
    assert client.client_creds['client_id'] == 'test-client-id'
    assert client.client_creds['client_secret'] == 'test-client-secret'
    assert client.client_creds['scopes'] == ['scope-a', 'scope-b']

    assert client.user_creds['access_token'] == 'test-access-token'
    assert client.user_creds['refresh_token'] == 'test-refresh-token'
    assert client.user_creds['scopes'] == ['scope-a', 'scope-b']
    assert client.user_creds['token_uri'] == 'https://oauth.test/token'

    assert client.gmail is None
    assert client.drive is None


async def test_get_new_email_returns_none_for_empty_inbox(client, fake_aiogoogle):
    stub_services(client)
    list_request = client.gmail.users.messages.list.return_value
    fake_aiogoogle.responses = {list_request: {}}

    result = await client.get_new_email()

    assert result is None
    client.gmail.users.messages.list.assert_called_once_with(
        userId='me', labelIds=['INBOX', 'UNREAD'])
    # Nothing was fetched or modified.
    client.gmail.users.messages.get.assert_not_called()
    client.gmail.users.messages.modify.assert_not_called()


async def test_get_new_email_returns_none_for_empty_messages_list(
        client, fake_aiogoogle):
    stub_services(client)
    list_request = client.gmail.users.messages.list.return_value
    fake_aiogoogle.responses = {list_request: {'messages': []}}

    assert await client.get_new_email() is None
    client.gmail.users.messages.modify.assert_not_called()


async def test_get_new_email_parses_headers(client, fake_aiogoogle):
    stub_services(client)
    messages = client.gmail.users.messages
    fake_aiogoogle.responses = {
        messages.list.return_value: {'messages': [{'id': 'msg-1'}]},
        messages.get.return_value: {
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'Anna <anna@example.com>'},
                    {'name': 'To', 'value': 'aktiva@lists.example.com'},
                    {'name': 'Subject', 'value': 'Veckomejl v.29'},
                    {'name': 'Mailing-list', 'value': 'list aktiva'},
                    {'name': 'Date', 'value': 'Sun, 19 Jul 2026 12:00:00 +0200'},
                ],
            },
        },
        messages.modify.return_value: {},
    }

    result = await client.get_new_email()

    assert result == {
        'subject': 'Veckomejl v.29',
        'sender': 'Anna <anna@example.com>',
        'recipient': 'aktiva@lists.example.com',
        'mailing_list': 'list aktiva',
    }
    messages.get.assert_called_once_with(
        userId='me',
        id='msg-1',
        format='metadata',
        metadataHeaders=['From', 'To', 'Subject', 'Date', 'Mailing-list'],
    )


async def test_get_new_email_missing_headers_are_none(client, fake_aiogoogle):
    stub_services(client)
    messages = client.gmail.users.messages
    fake_aiogoogle.responses = {
        messages.list.return_value: {'messages': [{'id': 'msg-1'}]},
        messages.get.return_value: {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Bara ett ämne'},
                ],
            },
        },
        messages.modify.return_value: {},
    }

    result = await client.get_new_email()

    assert result == {
        'subject': 'Bara ett ämne',
        'sender': None,
        'recipient': None,
        'mailing_list': None,
    }


async def test_get_new_email_marks_read_and_adds_label(client, fake_aiogoogle):
    stub_services(client)
    messages = client.gmail.users.messages
    fake_aiogoogle.responses = {
        messages.list.return_value: {'messages': [{'id': 'msg-1'}]},
        messages.get.return_value: {'payload': {'headers': []}},
        messages.modify.return_value: {},
    }

    await client.get_new_email()

    messages.modify.assert_called_once_with(
        userId='me',
        id='msg-1',
        json={
            'addLabelIds': ['test-label-id'],
            'removeLabelIds': ['UNREAD'],
        },
    )
    # The modify request was actually executed via as_user.
    assert messages.modify.return_value in fake_aiogoogle.as_user_calls


async def test_list_drive_folder_returns_result(client, fake_aiogoogle):
    stub_services(client)
    files = {'files': [{'name': 'Veckomejl v.29', 'mimeType': 'text/plain'}]}
    fake_aiogoogle.responses = {client.drive.files.list.return_value: files}

    result = await client.list_drive_folder('folder-123')

    assert result == files


async def test_list_drive_folder_queries_folder_sorted_by_created_time(
        client, fake_aiogoogle):
    stub_services(client)
    fake_aiogoogle.responses = {client.drive.files.list.return_value: {'files': []}}

    await client.list_drive_folder('folder-123')

    kwargs = client.drive.files.list.call_args.kwargs
    assert kwargs['q'] == "'folder-123' in parents and trashed = false"
    assert kwargs['orderBy'] == 'createdTime desc'


async def test_list_drive_folder_sort_by_name(client, fake_aiogoogle):
    stub_services(client)
    fake_aiogoogle.responses = {client.drive.files.list.return_value: {'files': []}}

    await client.list_drive_folder('folder-123', sort_by_name=True)

    kwargs = client.drive.files.list.call_args.kwargs
    assert kwargs['orderBy'] == 'name'
