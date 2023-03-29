import json
from datetime import datetime

import discord
from discord import commands, option
import streque


class Song(discord.Cog):
    song_group = commands.SlashCommandGroup("song", "Get information about songs in Flerstämt (starting notes, page number, sheet music, etc)")

    def __init__(self, bot):
        self.bot = bot
        with open("songs.json", "r") as f:
            self.songs = json.load(f)

    def create_embed(self, song):
        return discord.Embed(
            title=f"{song['page']}. {song['name']}",
            description="\n".join(song['alt']) if 'alt' in song else "",
            # url=f"https://www.streque.se/quotes/#quote-{quote['id']}",
            # timestamp=datetime.fromtimestamp(quote['timestamp']),
            fields=[
                discord.EmbedField(name=f"Tonart", value=song['chord'], inline=True),
                discord.EmbedField(name=f"Starttoner", value=", ".join(song['tones']), inline=True),
            ],
        )

    @song_group.command(description="Get information about the song in Flerstämt on a specific page.")
    @option(
        "page",
        description="The page number",
        min_value=8,
        max_value=188,
    )
    async def page(self, ctx, page: int):
        for song in self.songs:
            if int(song['page']) == page:
                await ctx.respond(embeds=[self.create_embed(song)])


def setup(bot):
    bot.add_cog(Song(bot))
