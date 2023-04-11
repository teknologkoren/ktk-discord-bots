import json
import sys

from aiogoogle.auth.creds import ClientCreds, UserCreds
from aiogoogle import Aiogoogle

from config import GMAIL_LABEL_SENT_TO_DISCORD


class GoogleAPIClient:
    def __init__(self):
        with open('token.json', 'r') as f:
            creds = json.load(f)

        self.client_creds = ClientCreds(
            client_id=creds['client_id'],
            client_secret=creds['client_secret'],
            scopes=creds['scopes'],
        )
        self.user_creds = UserCreds(
            access_token=creds['token'],
            refresh_token=creds['refresh_token'],
            scopes=creds['scopes'],
            token_uri=creds['token_uri'],
        )
        self.gmail = None
        self.drive = None

    # Refreshes user access token if required.
    async def refresh(self, aiogoogle):
        is_refreshed, user_creds = await aiogoogle.oauth2.refresh(
            aiogoogle.user_creds, client_creds=aiogoogle.client_creds)
        # If credentials were refreshed, update them both in aiogoogle and in self
        # (so we don't need to refresh again next time we instantiate Aiogoogle).
        if is_refreshed:
            aiogoogle.user_creds = user_creds
            self.user_creds = user_creds

    # Use service discovery to create a Gmail and a Drive client.
    async def initialize(self):
        if not self.gmail or not self.drive:
            async with Aiogoogle(
                    user_creds=self.user_creds,
                    client_creds=self.client_creds) as aiogoogle:

                await self.refresh(aiogoogle)
                self.gmail = await aiogoogle.discover('gmail', 'v1')
                self.drive = await aiogoogle.discover('drive', 'v3')

    # Gets one new message from the inbox. If there is none, returns None.
    async def get_new_email(self):
        await self.initialize()
        async with Aiogoogle(
                user_creds=self.user_creds,
                client_creds=self.client_creds) as aiogoogle:

            await self.refresh(aiogoogle)

            inbox = await aiogoogle.as_user(
                self.gmail.users.messages.list(
                    userId='me',
                    labelIds=['INBOX', 'UNREAD'],
                ),
                raise_for_status=True,
            )

            if 'messages' not in inbox or not inbox['messages']:
                return None

            message = await aiogoogle.as_user(
                self.gmail.users.messages.get(
                    userId='me',
                    id=inbox['messages'][0]['id'],
                    format='metadata',
                    metadataHeaders=[
                        'From', 'To', 'Subject', 'Date', 'Mailing-list',
                    ],
                ),
                raise_for_status=True,
            )

            subject = None
            sender = None
            recipient = None
            mailing_list = None
            for header in message['payload']['headers']:
                if header['name'] == 'From':
                    sender = header['value']
                if header['name'] == 'To':
                    recipient = header['value']
                if header['name'] == 'Subject':
                    subject = header['value']
                if header['name'] == 'Mailing-list':
                    mailing_list = header['value']

            # Mark as read, and add sent to discord label.
            await aiogoogle.as_user(
                self.gmail.users.messages.modify(
                    userId='me',
                    id=inbox['messages'][0]['id'],
                    json={
                        'addLabelIds': [GMAIL_LABEL_SENT_TO_DISCORD],
                        'removeLabelIds': ['UNREAD'],
                    },
                ),
                raise_for_status=True,
            )

            return {
                'subject': subject,
                'sender': sender,
                'recipient': recipient,
                'mailing_list': mailing_list,
            }

    # List up to 1000 files in a "My Drive" folder (not from a "Shared Drive")
    # By default sorts by createdTime descending. If `sort_by_name` is set to
    # true, instead sort by name in ascending order.
    async def list_drive_folder(self, folder_id, sort_by_name=False):
        await self.initialize()
        async with Aiogoogle(user_creds=self.user_creds) as aiogoogle:
            await self.refresh(aiogoogle)

            result = await aiogoogle.as_user(
                self.drive.files.list(
                    corpora="user",
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="files(name,webViewLink,webContentLink,mimeType)",
                    orderBy="name" if sort_by_name else "createdTime desc",
                    pageSize=1000,
                ),
                raise_for_status=True,
            )
            return result
