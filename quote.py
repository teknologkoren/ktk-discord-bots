import re
from datetime import datetime

import discord
from discord import commands, option
import streque


class Quote(discord.Cog):
    quote = commands.SlashCommandGroup("quote", "Post quotes from Streque.")
    quote_id_pattern = re.compile(r"#quote-(\d+)")

    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, quote):
        return discord.Embed(
            title=f"Citat #{quote['id']}",
            description=quote['text'],
            url=f"https://www.streque.se/quotes/#quote-{quote['id']}",
            timestamp=datetime.fromtimestamp(quote['timestamp']),
            fields=[
                discord.EmbedField(name=f"– {quote['who']}", value="")
            ],
        )

    @quote.command(description="Lookup a Streque quote by its id, for example \"1971\".")
    @option(
        "quote_id",
        description="The id of the quote, without the \"#\", from the bottom-right of the quote on the Streque website.",
        min_value=1,
    )
    async def id(self, ctx, quote_id: int):
        try:
            result = await streque.get_quote(int(quote_id))
            await ctx.respond(embeds=[self.create_embed(result)])
        except:
            await ctx.respond("I couldn't find the quote you were looking for...")

    @quote.command(description="Post a random Streque quote.")
    async def random(self, ctx):
        try:
            result = await streque.get_random_quote()
            await ctx.respond(embeds=[self.create_embed(result)])
        except:
            await ctx.respond("I didn't manage to get a random quote. Please inform the webmaster so they can fix me.")


    @quote.command(description="Lookup a Streque quote by its permalink, e.g. \"https://www.streque.se/quotes/#quote-1971\".")
    @option(
        "url",
        description="The permalink of the quote (from the bottom-right of the quote on the Streque website).",
    )
    async def url(self, ctx, url):
        match = self.quote_id_pattern.search(url)
        if len(match.groups()) < 1:
            await ctx.respond("You seem to have provided an invalid quote URL.")
        else:
            try:
                result = await streque.get_quote(int(match.group(1)))
                await ctx.respond(embeds=[self.create_embed(result)])
            except:
                await ctx.respond("I couldn't find the quote you were looking for...")


def setup(bot):
    bot.add_cog(Quote(bot))
