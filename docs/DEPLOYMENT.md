# Deploying the bots

The bots run as a Docker container (same pattern as
[flasquelistan](https://github.com/teknologkoren/flasquelistan)): a single
Python process started by `docker compose`, restarted automatically by Docker
on crashes and on boot (`restart: unless-stopped`). All runtime state and
secrets — `config.py`, `group_config.py`, `songs.json`, `credentials.json`,
`token.json` — live as plain files in `instance/` in the checkout, which is
bind-mounted into the container. Nothing secret is baked into the image.

The bots only make outbound connections (Discord, Streque, the Google APIs),
so no ports are published and no reverse proxy is involved.

## Deploying a new version

```
ssh <you>@<server>
cd <checkout>
git pull
docker compose up --build -d
```

Verify that the bots come online in Discord. If they don't:

```
docker compose logs --tail 50 bot
```

`docker compose logs` shows the process stdout. The Discord library
additionally logs to `discord.log` inside the container (truncated on every
restart): `docker compose exec bot tail -50 discord.log`.

### Rollback

```
git log --oneline           # find the last good commit
git reset --hard <commit>
docker compose up --build -d
```

## First-time setup on a server

1. Install Docker (with the compose plugin) and clone this repo.
2. Populate `instance/` as described in the [README](../README.md):
   `config.py` (mandatory), and optionally `group_config.py`, `songs.json`,
   `credentials.json` + `token.json` for the Google integration. The Google
   OAuth flow (`bot/scripts/google_creds.py`) needs a browser, so run it on
   your own machine and copy the resulting `instance/token.json` to the
   server.
3. `docker compose up --build -d`

Notes:

- **The container runs as UID 1000.** It needs to be able to read the mounted
  `instance/` directory (and write to it, for `token.json` refreshes). If the
  checkout is owned by another UID on the host, set `user:` in a compose
  override.
- **Migrating from the old tmux setup:** stop the old manually-started
  process first (`tmux attach`, Ctrl-C, exit), then start the container. Two
  bot processes with the same tokens must not run at the same time. The
  `instance/` directory from the tmux-era checkout is used as-is; no
  conversion is needed.
