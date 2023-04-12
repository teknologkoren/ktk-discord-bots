import random
import re
import traceback
import sys
from datetime import datetime

import discord
from discord import commands, option

from bot.clients import streque


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
        description="The id of the quote, without the \"#\", from the bottom-right of "
            "the quote on the Streque website.",
        min_value=1,
    )
    async def id(self, ctx, quote_id: int):
        try:
            result = await streque.get_quote_by_id(int(quote_id))
            await ctx.respond(embeds=[self.create_embed(result)])
        except:
            print(traceback.format_exc(), file=sys.stderr)
            await ctx.respond("I couldn't find the quote you were looking for...")

    @quote.command(description="Post a random Streque quote.")
    async def roulette(self, ctx):
        try:
            result = await streque.get_random_quote()
            await ctx.respond(embeds=[self.create_embed(result)])
        except:
            print(traceback.format_exc(), file=sys.stderr)
            await ctx.respond(
                "I didn't manage to get a random quote. Please inform the webmaster so "
                "they can fix me."
            )

    @quote.command(
        description="Lookup a Streque quote by its permalink, e.g. "
            "\"https://www.streque.se/quotes/#quote-1971\"."
    )
    @option(
        "url",
        description="The permalink of the quote (from the bottom-right of the quote on "
            "the Streque website).",
    )
    async def url(self, ctx, url):
        match = self.quote_id_pattern.search(url)
        if len(match.groups()) < 1:
            await ctx.respond("You seem to have provided an invalid quote URL.")
        else:
            try:
                result = await streque.get_quote_by_id(int(match.group(1)))
                await ctx.respond(embeds=[self.create_embed(result)])
            except:
                print(traceback.format_exc(), file=sys.stderr)
                await ctx.respond("I couldn't find the quote you were looking for...")

    @quote.command(
        description="Post the latest quote."
    )
    async def latest(self, ctx):
        try:
            result = await streque.get_latest_quote()
            await ctx.respond(embeds=[self.create_embed(result)])
        except:
            print(traceback.format_exc(), file=sys.stderr)
            await ctx.respond(
                "I didn't manage to fetch the latest quote. Please inform the webmaster so "
                "they can fix me."
            )

    @quote.command(
        description="Post a random quote containing your search query."
    )
    @option(
        "query",
        description="Your search term. Upper/lower-case is irrelevant, but besides that "
            "the search is exact.",
    )
    async def search(self, ctx, query):
        try:
            quotes = await streque.get_all_quotes()
        except:
            print(traceback.format_exc(), file=sys.stderr)
            await ctx.respond(
                "I didn't manage to fetch any quotes. Please inform the webmaster so "
                "they can fix me."
            )

        matches = []
        for quote in quotes:
            if query.lower() in quote['text'].lower() or query.lower() in quote['who'].lower():
                matches.append(quote)

        if matches:
            result = random.choice(matches)
            await ctx.respond(
                f"Sökte efter: *{query}*",
                embeds=[self.create_embed(result)]
            )
        else:
            await ctx.respond("I couldn't find any quotes matching your query.")


def setup(bot):
    bot.add_cog(Quote(bot))
