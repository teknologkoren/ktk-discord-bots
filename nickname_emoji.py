import sys

import streque
from config import DISCORD_GUILD_ID

# TODO: 🇷🇺 and 🇫🇮 do not seem to work as intended.
managed_emojis = ('🍺', '🍻', '👌', '🕺', '😟', '🤢', '😵', '💀', '🇷🇺', '🇫🇮')


async def set_emoji(member, new_emoji):
    current_nick = member.nick
    if current_nick is None:
        print(f"User {member.id} has no nick, so not setting emoji.", file=sys.stderr)
        return

    has_emoji = current_nick[0] in managed_emojis
    current_emoji = current_nick[0] if has_emoji else None

    new_nick = current_nick
    if has_emoji and new_emoji is None:
        # Remove the emoji prefix
        new_nick = current_nick[1:]
    elif has_emoji and new_emoji != current_emoji:
        # Switch to the new emoji
        new_nick = new_emoji + current_nick[1:]
    elif not has_emoji and new_emoji is not None:
        # Add emoji
        new_nick = new_emoji + current_nick

    if current_nick != new_nick:
        print(f"Changing nick from {current_nick} to {new_nick}", file=sys.stderr)
        await member.edit(nick=new_nick, reason="Syncing nickname with Streque emoji.")


async def handle_balance_change(bot, data):
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    member = await guild.fetch_member(data['discord_user_id'])
    await set_emoji(member, data['new_emoji'])


async def periodic_update(bot):
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    async for member in guild.fetch_members():
        if member.nick is None:
            continue

        if member.nick[0] in managed_emojis:
            streque_user = await streque.get_user_by_discord(member.id)
            await set_emoji(member, streque_user['bac_emoji'])
