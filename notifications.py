import discord
import streque


async def handle_notification(bot, notification):
    discord_user_id = notification['discord_user_id']
    if discord_user_id is None:
        print(f"User {notification['user_id']} is not connected to Discord.")
        return

    view = MarkReadView()
    view.children[0].custom_id = f"notification-{notification['notification_id']}"

    user = await bot.fetch_user(discord_user_id)
    channel = await user.create_dm()
    await channel.send(notification['text'], view=view)
    await streque.mark_notification_sent(notification['notification_id'])


class MarkReadView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Markera som läst", style=discord.ButtonStyle.primary, emoji="✅")
    async def button_callback(self, button, interaction):
        await streque.mark_notification_acknowledged(
            interaction.custom_id[len("notification-"):])
        button.disabled = True
        await interaction.response.edit_message(view=self)