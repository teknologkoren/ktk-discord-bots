# ktk-discord-bots

This repository is home to KTK's two Discord bots: Streque and Körbot. Streque provides integration with [flasquelistan](https://github.com/teknologkoren/flasquelistan), while Körbot provides various non-Streque related services such as playing the starting notes of any song in our standard repertoire in a voice channel, or notifying people that a new weekly email has arrived.


## Setting up a development environment
This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies.
Install uv, then create the virtual environment and install all dependencies
(including the dev/test dependencies) with:

```sh
uv sync
```

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. To
add/remove a dependency, edit `pyproject.toml` and run `uv sync` (or use
`uv add`/`uv remove`), then commit the updated lockfile.

## Running the tests
The unit tests live in `tests/`, one file per bot module. They do not need any
real configuration: `tests/conftest.py` installs a fake `instance.config` (and
`instance.group_config`) before the bot modules are imported, and all Discord
and HTTP interactions are mocked.

Run the suite from the repo root:

```sh
uv run pytest
```

## Configuration
All possible config variables are listed in `config.py.template`. Please make a copy of it to `instance/config.py` and fill out the values. Some of them are mandatory for the bots to run, while others are just needed for some of the functionality to be enabled.

### Integration with Discord
We are using Pycord to interface with Discord. In order for the bots to even run, you need Discord bot account tokens. See [Pycord's documentation](https://docs.pycord.dev/en/stable/discord.html) for instructions on how to create a Discord application as well as bot accounts.

Two different Discord applications and bot accounts are used for Körbot and the Streque bot in prod, but they both live in the same Python process. For developement and test deployments, only one bot account is required. Just leave `CHOIR_BOT_TOKEN` unset, and all functionality will be surfaced through the bot with token `STREQUE_BOT_TOKEN`.

If you'd like to avoid creating a new Discord server for testing, you can ask to be added to the existing test server created by @grensjo.

### Integration with Strequelistan
To integrate with [flasquelistan](https://github.com/teknologkoren/flasquelistan), you need an API key with admin privileges. To create one, navigate to your edit profile page, click on "Manage API keys", and follow the instructions. For developement and testing purposes, please do this for a local test instance of flasquelistan, not the prod version.

Then set `STREQUE_BASE_URL` to the URL of your instance, and `STREQUE_TOKEN` to your API token.

This is not strictly related to the bot repo, but note that in order to test the Streque join flow, HTTPS is required. For local test runs a TLS tunnel to your computer can be set up e.g. using [ngrok](https://ngrok.com/). Make sure to add `https://your-ngrok-streque-domain/discord/callback` as a callback link in the Discord application. (You can still keep localhost:port in `instance/config.py`.)

### Integration with Gmail / Google Drive
The bots use the Gmail API to look for new emails to notify about, and the Google Drive API to list folder contents in Drive in order to post direct links to content in Discord. If you want a test account in our Workspace organization to work with, ask @grensjo.

Two files are needed to enable the Google APIs. Firstly, you need a `instance/credentials.json` file for a Google Cloud project. You can create your own or ask grensjo@ to use our existing project. Secondly, you need OAuth2 tokens for the account you want to use the API as. This can be obtained using the `google_creds.py` script. Run the script, log in to the account in a browser when prompted, and a token with the needed scopes will be written to `instance/token.json`.

### Song-searching and start notes
In order to enable the song-searching command, please copy `songs.json.template` into `instance/songs.json`. Here you can add additional songs besides the ones in Flerstämt, as well as add extra metadata and links related to the songs.

### On-join role assignment
[flasquelistan](https://github.com/teknologkoren/flasquelistan) itself manages some Discord roles, namely Aktiva, the ones corresponding to groups on Streque, and Okänd. Okänd will be assigned to users who are not in any of the synced groups (but this case is rare, since the join link is only shown for users in a synced group). On the group admin page it can be configured which groups will be synced with Discord.

The flasquelistan-managed roles will be assigned on join, as well as updated whenever a user's profile is updated (since that could indicate a group change), or if a user reconnects to Discord or removes their Discord account from Streque.

Other roles will need to be managed manually by Discord admins, but to make this a bit easier when many people join the server at the same time, there is a mechanism in the bot to do a one-time role assignment on join. In order to enable this, copy `group_config.py.template` to `instance/group_config.py` and populate it with role ids and member full names. The names need to exactly match the full names of the Streque users.

## Running the bots
Simply run `uv run app.py` with the repo root as working directory to start the bots. They will be online for as long as the script runs.

### Docker
The bots can also be run the same way production does, in a Docker container:

```sh
docker compose up --build -d
```

The `instance/` directory is bind-mounted into the container, so the
configuration described above is picked up as-is. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for details on the production setup.
For day-to-day development, plain `uv run app.py` remains the quickest loop.

## Documentation

- [Deploying to production](docs/DEPLOYMENT.md) — Docker-based deployment
