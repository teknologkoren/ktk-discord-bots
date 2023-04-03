import aiohttp
import discord
from config import STREQUE_URL, STREQUE_TOKEN
from config import DISCORD_GUILD_ID, DISCORD_VIP_ROLE_ID, DISCORD_VIP_CHANNEL_ID


# Make a GET request, check that it was successful, and return the response content
# as JSON.
async def get_request(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'{STREQUE_URL}{path}',
            headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ) as response:
            response.raise_for_status()
            return await response.json()


# Make a POST request, check that it was successful, and ignore any response content.
async def post_request(path):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{STREQUE_URL}{path}',
            headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ) as response:
            response.raise_for_status()
            return


async def get_random_quote():
    return await get_request('/quotes/random')


async def get_quote(quote_id):
    return await get_request(f'/quotes/{quote_id}')


async def mark_notification_sent(notification_id):
    await post_request(
        f'/notifications/{notification_id}/mark_sent')


async def mark_notification_acknowledged(notification_id):
    await post_request(
        f'/notifications/{notification_id}/mark_acknowledged')


def kr(ören):
    s = round(ören/100)
    return f"{s} kr"


async def get_dm_channel(bot, discord_user_id):
    user = await bot.fetch_user(discord_user_id)
    return await user.create_dm()


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


async def handle_balance_change(bot, balance_change):
    discord_user_id = balance_change['discord_user_id']
    if discord_user_id is None:
        print(f"User {balance_change['user_id']} is not connected to Discord.")
        return

    old = balance_change['old_balance']
    new = balance_change['new_balance']

    # Is no longer VIP (balance below 1000 kr)
    if old >= 100_000 and new < 100_000:
        ch = await get_dm_channel(bot, discord_user_id)
        await ch.send(
            f"Ditt Streque-saldo gick just ner till {kr(new)}, vilket "
            "betyder att du ej längre är på VIP-listan?! Men oroa dig ej, "
            "problemet är enkelt löst genom att föra över lite pengar "
            "till ditt konto! <a:smartgif:1089984415821746270>")
        await remove_from_vip(bot, discord_user_id)

    # Is now VIP (balance above 1000 kr)
    if old < 100_000 and new >= 100_000:
        ch = await get_dm_channel(bot, discord_user_id)
        await ch.send(
            f"Grattis, ditt Streque-saldo gick just upp till {kr(new)}, vilket betyder "
            "att du har kvalificerat dig till VIP-listan samt fått access till den exklusiva "
            f"kanalen <#{DISCORD_VIP_CHANNEL_ID}>! <:hype:1090539895052845096>")
        await add_to_vip(bot, discord_user_id)

    # Balance at 0 kr or below
    if old > 0 and new <= 0:
        ch = await get_dm_channel(bot, discord_user_id)
        await ch.send(
            f"Du har slut pengar på ditt Streque-konto, och ligger nu {kr(-new)} back. Dags att fylla på!")
    # Balance below 100 kr
    elif old >= 10_000 and new < 10_000:
        ch = await get_dm_channel(bot, discord_user_id)
        await ch.send(
            f"Det börjar bli ont om pengar på ditt Streque-konto, du har för närvarande {kr(new)} kvar. Dags att fylla på?")


async def handle_notification(bot, notification):
    discord_user_id = notification['discord_user_id']
    if discord_user_id is None:
        print(f"User {notification['user_id']} is not connected to Discord.")
        return

    view = MarkReadView()
    view.children[0].custom_id = f"notification-{notification['notification_id']}"

    channel = await get_dm_channel(bot, discord_user_id)
    await channel.send(notification['text'], view=view)
    await mark_notification_sent(notification['notification_id'])


class MarkReadView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Markera som läst", style=discord.ButtonStyle.primary, emoji="✅")
    async def button_callback(self, button, interaction):
        await mark_notification_acknowledged(
            interaction.custom_id[len("notification-"):])
        button.disabled = True
        await interaction.response.edit_message(view=self)
