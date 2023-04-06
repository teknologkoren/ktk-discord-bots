import json

import discord
from discord import commands, option

from config import FLERSTÄMT_PDF_URL, FLERSTÄMT_MIDI_URL


class Song(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("songs.json", "r") as f:
            self.songs = json.load(f)

        # Lookup table from any valid search query (name, alternative names,
        # page number followed by name) to song dict.
        self.lookup = {}

        # Lookup table from page number to song dict.
        self.by_page = {}

        # Lookup table from id to song dict.
        self.by_id = {}

        for song in self.songs:
            self.by_id[song['id']] = song

            if song.get('page', None) is not None:
                self.lookup[f"{song['page']}. {song['name']}"] = song
                self.by_page[song['page']] = song

            self.lookup[song['name']] = song
            if 'alt' in song:
                for alt in song['alt']:
                    self.lookup[alt] = song

    async def autocomplete_callback(self, ctx: discord.AutocompleteContext):
        results = [key for key in self.lookup.keys()
                   if not ctx.value or key.lower().startswith(ctx.value.lower())]

        # Shortcut for finding songs not in Flerstämt
        if ctx.value and ctx.value.lower()[0] == 'x':
            results = [song['name'] for song in self.songs if not song.get('page', None)]

        # If empty query or searching by page number, sort in numeric order.
        if len(ctx.value) == 0 or ctx.value.isnumeric():
            return sorted([key for key in results if key[0:1].isnumeric()], key=lambda song: int(song[:song.find('.')]))
        else:
            return sorted(results)

    @commands.command(
        description="Get information about a song. Either from Flerstämt, or from a "
        "selected subset of certified bangers.")
    @option(
        "query",
        description='Song title, beginning lyrics, or page number in Flerstämt.',
        autocomplete=autocomplete_callback
    )
    async def song(self, ctx, query: str):
        result = self.lookup.get(query, None)
        if result is None:
            result = self.by_page.get(query, None)

        if result is None:
            await ctx.respond("Jag kunde inte hitta sången du letar efter. :(")
        else:
            await ctx.respond(
                embeds=[self.create_embed(result)],
                view=self.create_song_view(result),
            )

            # Easter egg
            if result['name'] == "Die Beredsamkeit" and ctx.user.id == 242287639334617090:
                with open("images/die_beredsamkeit.jpg", "rb") as fp:
                    await ctx.channel.send(file=discord.File(fp))

    def create_embed(self, song):
        if 'page' in song and song['page']:
            title = f"{song['page']}. {song['name']}"
        else:
            title = song['name']
        return discord.Embed(
            title=title,
            description="\n".join(song['alt']) if 'alt' in song else "",
            fields=[
                discord.EmbedField(
                    name=f"Startackord / tonart",
                    value=song['chord'],
                    inline=True
                ),
                discord.EmbedField(
                    name=f"Starttoner",
                    value=", ".join(song['tones']),
                    inline=True
                ),
            ],
        )

    def create_song_view(self, song):
        view = discord.ui.View(timeout=None)

        view.add_item(discord.ui.Button(
            emoji="<:stamgaffel:1089692591672537179>",
            label="Ta ton",
            style=discord.ButtonStyle.primary,
            custom_id=f"ta-ton-{song['id']}",
        ))

        # Sheet music link
        if song.get('url', None):
            view.add_item(discord.ui.Button(
                emoji="<:pdf:1092947757498650805>",
                label="Not",
                url=song['url'],
            ))

        # Flerstämt links
        if song.get('page', None):
            view.add_item(discord.ui.Button(
                emoji="<:flerstamt:1093319826925162588>",
                label="Flerstämt",
                url=FLERSTÄMT_PDF_URL,
            ))
            view.add_item(discord.ui.Button(
                emoji="<:drive:1092948377794252941>",
                label="MIDI-mapp",
                url=FLERSTÄMT_MIDI_URL,
            ))

        return view


def setup(bot):
    bot.add_cog(Song(bot))
