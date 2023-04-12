import discord
from bot.clients import streque


def create_notification_view(notification_id, button_disabled=False):
    return discord.ui.View(
        discord.ui.Button(
            emoji="✅",
            label="Markera som läst",
            style=discord.ButtonStyle.primary,
            custom_id=f"notification-{notification_id}",
            disabled=button_disabled,
        ),
        discord.ui.Button(
            emoji="<:streque:1090714544634085416>",
            label="Visa alla",
            url="https://www.streque.se/notifications",
        ),
        timeout=None
    )


async def handle_notification(bot, notification):
    discord_user_id = notification['discord_user_id']
    if discord_user_id is None:
        print(f"User {notification['user_id']} is not connected to Discord.")
        return

    view = create_notification_view(notification['notification_id'])

    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(notification['text'], view=view)
    await streque.mark_notification_sent(notification['notification_id'])


async def mark_read_callback(interaction):
    notification_id = interaction.custom_id[len("notification-"):]
    await streque.mark_notification_acknowledged(notification_id)
    await interaction.response.edit_message(
        view=create_notification_view(notification_id, button_disabled=True))
