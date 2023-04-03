from datetime import datetime
import streque
import sys

from config import DISCORD_GUILD_ID, DISCORD_BIRTHDAY_CHANNEL_ID, DISCORD_ACTIVE_ROLE_ID

async def congratulate(bot):
    now = datetime.now()
    users = await streque.get_birthday_users(now.month, now.day)
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    active_role = guild.get_role(DISCORD_ACTIVE_ROLE_ID)

    user_ids = []
    for user in users:
        if user['discord_user_id'] is not None:
            member = await guild.fetch_member(user['discord_user_id'])

            # Only congratulate active members.
            if active_role in member.roles:
                user_ids.append(user['discord_user_id'])
            else:
                print(
                    f"{user['full_name']} fyller år men är inte aktiv medlem.", file=sys.stderr)
        else:
            print(
                f"{user['full_name']} fyller år men är inte med i Discorden.", file=sys.stderr)
    
    if not user_ids:
        # There is nobody to congratulate today :(
        print(f"Ingen fyller år idag. :(", file=sys.stderr)
        return

    # Construct congratulations message.
    mention_list = [f"<@{user_id}>" for user_id in user_ids]
    if len(user_ids) == 1:
        message = f"<@{user_ids[0]}>"
    else:
        message = ", ".join(mention_list[:-1]) + " och " + mention_list[-1]
    message += " fyller år idag! Stort grattis! :partying_face:"

    # Post it in the configured channel.
    print(message, file=sys.stderr)
    channel = await guild.fetch_channel(DISCORD_BIRTHDAY_CHANNEL_ID)
    await channel.send(message)
