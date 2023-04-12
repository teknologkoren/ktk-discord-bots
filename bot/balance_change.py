from instance.config import DISCORD_GUILD_ID, DISCORD_VIP_ROLE_ID, DISCORD_VIP_CHANNEL_ID


async def add_to_vip(bot, user_id):
    # Add to role
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    member = await guild.fetch_member(user_id)
    role = guild.get_role(DISCORD_VIP_ROLE_ID)
    await member.add_roles(role)

    # Announce in #vip
    channel = await guild.fetch_channel(DISCORD_VIP_CHANNEL_ID)
    await channel.send(f"<@{user_id}> är nu med på VIP-listan. Välkommen! :partying_face:")


async def remove_from_vip(bot, user_id):
    # Announce in #vip
    guild = await bot.fetch_guild(DISCORD_GUILD_ID)
    channel = await guild.fetch_channel(DISCORD_VIP_CHANNEL_ID)
    await channel.send(f"<@{user_id}> är inte längre VIP. :pensive:")

    # Remove from role
    member = await guild.fetch_member(user_id)
    role = guild.get_role(DISCORD_VIP_ROLE_ID)
    await member.remove_roles(role)


def kr(ören):
    s = round(ören/100)
    return f"{s} kr"


async def send_vip_status_gained_alert(bot, discord_user_id, balance):
    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(
        f"Grattis, ditt Streque-saldo gick just upp till {kr(balance)}, vilket betyder "
        "att du har kvalificerat dig till VIP-listan samt fått access till den exklusiva "
        f"kanalen <#{DISCORD_VIP_CHANNEL_ID}>! <:hype:1090539895052845096>")


async def send_vip_status_lost_alert(bot, discord_user_id, balance):
    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(
        f"Ditt Streque-saldo gick just ner till {kr(balance)}, vilket "
        "betyder att du ej längre är på VIP-listan?! Men oroa dig ej, "
        "problemet är enkelt löst genom att föra över lite pengar "
        "till ditt konto! <a:smartgif:1089984415821746270>")


async def send_low_balance_alert(bot, discord_user_id, balance):
    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(
        f"Det börjar bli ont om pengar på ditt Streque-konto, du har för "
        "närvarande {kr(balance)} kvar. Dags att fylla på?")


async def send_negative_balance_alert(bot, discord_user_id, balance):
    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(
        f"Du har slut pengar på ditt Streque-konto, och ligger nu {kr(-balance)} "
        "back. Dags att fylla på!")


async def handle_balance_change(bot, balance_change):
    discord_user_id = balance_change['discord_user_id']
    if discord_user_id is None:
        print(f"User {balance_change['user_id']} is not connected to Discord.")
        return

    old = balance_change['old_balance']
    new = balance_change['new_balance']

    # Is no longer VIP (balance below 1000 kr)
    if old >= 100_000 and new < 100_000:
        await send_vip_status_lost_alert(bot, discord_user_id, new)
        await remove_from_vip(bot, discord_user_id)

    # Is now VIP (balance above 1000 kr)
    if old < 100_000 and new >= 100_000:
        await send_vip_status_gained_alert(bot, discord_user_id, new)
        await add_to_vip(bot, discord_user_id)

    # Balance at 0 kr or below
    if old > 0 and new <= 0:
        send_negative_balance_alert(bot, discord_user_id, new)
    # Balance below 100 kr
    elif old >= 10_000 and new < 10_000:
        send_low_balance_alert(bot, discord_user_id, new)
