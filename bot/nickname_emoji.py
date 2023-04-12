import sys
import traceback

from aiohttp.client_exceptions import ClientResponseError

from bot.clients import streque
from instance.config import DISCORD_GUILD_ID

# TODO: 🇷🇺 and 🇫🇮 do not seem to work as intended.
managed_emojis = ('🍺', '🍻', '👌', '🕺', '😟', '🤢', '😵', '💀')


def map_emoji(emoji):
    # This feature does not yet support 32-bit emojis. Let's replace the flags with
    # the skull for now, as a quick fix.
    if emoji == '🇷🇺' or emoji == '🇫🇮':
        return '💀'
    else:
        return emoji


async def set_emoji(member, new_emoji):
    new_emoji = map_emoji(new_emoji)
    current_nick = member.display_name
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
        print(
            f"Changing nick from {current_nick} to {new_nick}", file=sys.stderr)
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
            try:
                streque_user = await streque.get_user_by_discord(member.id)
                await set_emoji(member, streque_user['bac_emoji'])
            except ClientResponseError as e:
                if e.code == 404:
                    print(
                        f"WARNING: Discord user {member.nick} (#{member.nick}) is not "
                        "connected to Streque.", file=sys.stderr)
                else:
                    print(traceback.format_exc(), file=sys.stderr)
