FROM python:3.13.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

# ffmpeg decodes the start-note wav files (discord.FFmpegPCMAudio) and
# libopus0 encodes the audio py-cord sends to Discord voice channels.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libopus0 && \
    rm -rf /var/lib/apt/lists/*

# Venv outside /app so a dev bind mount of the repo does not shadow it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependency layer: cached unless the lockfile changes. The project is
# "virtual" in uv.lock, so this installs dependencies only.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --compile-bytecode

COPY . .

# UID 1000 matches the typical owner of the bind-mounted instance/ directory
# on the host; override with `user:` in compose if not. /app itself must be
# writable because the bot creates discord.log in the working directory.
RUN useradd --create-home --uid 1000 app && chown app:app /app
USER app

CMD ["python", "app.py"]
