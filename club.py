import json
import discord
from discord import commands, option

from config import CARL_REACTION_ROLE_CHANNEL_ID, CARL_REACTION_ROLE_MESSAGE_ID, DISCORD_CLUB_CATEGORY_ID


class Club(discord.Cog):
    club_group = commands.SlashCommandGroup("club", "Manage club chats")

    def __init__(self, bot):
        self.bot = bot

    @club_group.command(description="Command to help admins with creating a new club chat.")
    @option(
        "emoji",
        description="Emoji of the club. Will be used in the channel name and in the info message.",
    )
    @option(
        "name",
        description="Name of the club. Will be used for the role name and in the info message and topic.",
    )
    @option(
        "slug",
        description="Lower-case no-space version of the club name. Will be used for the channel name.",
    )
    @option(
        "description",
        description="Description of the club to be used in the info message and the channel topic.",
    )
    async def add(self, ctx, emoji: str, name: str, slug: str, description: str):
        # Check that the user has permission to edit roles and channels.
        if ctx.guild is None:
            await ctx.respond("Detta kommando kan endast användas från en server-kanal.")
            return
        if not ctx.user.guild_permissions.manage_guild:
            await ctx.respond("Du har ej behörighet att köra detta kommando, vänligen be en admin att hjälpa dig.")
            return

        reason = f"Creating new club chat {name}."

        # Create a role needed to access the club chat.
        role = await ctx.guild.create_role(
            name=name, mentionable=True, reason=reason)

        # Create a channel for the club chat, in the club category.
        category = await ctx.guild.fetch_channel(DISCORD_CLUB_CATEGORY_ID)
        await ctx.guild.create_text_channel(
            f"{emoji}{slug}",
            reason=reason,
            category=category,
            topic=description,
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True)})

        # Get the current role info embed, and add the new role.
        role_channel = await ctx.guild.fetch_channel(CARL_REACTION_ROLE_CHANNEL_ID)
        reaction_msg = await role_channel.fetch_message(CARL_REACTION_ROLE_MESSAGE_ID)
        club_embed = reaction_msg.embeds[0].to_dict()
        club_embed['fields'].append({
            'name': f'{emoji}: {name}',
            'value': description,
            'inline': False
        })

        # Respond with instructions to finish creating the club chat.
        await ctx.respond(f"Din nya klubbchatt {name} är nästan färdig! Tyvärr lyssnar Carl "
                          "inte på Körbot utan bara på riktiga användare. Därför behöver du "
                          "kopiera och klistra in följande två kommandon:")
        await ctx.send(
            f"!ecembed {CARL_REACTION_ROLE_MESSAGE_ID} {CARL_REACTION_ROLE_CHANNEL_ID} {json.dumps(club_embed)}")
        await ctx.send(
            f"!reactionrole add {CARL_REACTION_ROLE_CHANNEL_ID} {CARL_REACTION_ROLE_MESSAGE_ID} {emoji} <@&{role.id}>")


def setup(bot):
    bot.add_cog(Club(bot))
