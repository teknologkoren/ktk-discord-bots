import json
from datetime import datetime

import discord
from discord import commands, option

import player
from config import FLERSTÄMT_PDF_URL, FLERSTÄMT_MIDI_URL


class Song(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("songs.json", "r") as f:
            self.songs = json.load(f)

        self.lookup = {}
        self.by_page = {}
        for song in self.songs:
            if song['page'] is not None:
                self.lookup[f"{song['page']}. {song['name']}"] = song
                self.by_page[song['page']] = song
            self.lookup[song['name']] = song

            if 'alt' in song:
                for alt in song['alt']:
                    self.lookup[alt] = song

    def create_embed(self, song):
        if 'page' in song and song['page']:
            title = f"{song['page']}. {song['name']}"
        else:
            title = song['name']
        return discord.Embed(
            title=title,
            description="\n".join(song['alt']) if 'alt' in song else "",
            fields=[
                discord.EmbedField(name=f"Startackord / tonart", value=song['chord'], inline=True),
                discord.EmbedField(name=f"Starttoner", value=", ".join(song['tones']), inline=True),
            ],
        )
    
    async def autocomplete_page(self, ctx: discord.AutocompleteContext):
        # results = [key for key in self.lookup.keys() if key.startswith(ctx.value)]
        results = [key for key in self.lookup.keys() if not ctx.value or key.lower().startswith(ctx.value.lower())]

        # If searching by page number, sort in numeric order.
        if len(ctx.value) == 0 or ctx.value.isnumeric():
            return sorted([key for key in results if key[0:1].isnumeric()], key=lambda song: int(song[:song.find('.')]))
        else:
            return sorted(results)


    @commands.command(description="Get information about a song. Either from Flerstämt, or from a selected subset of certified bangers.")
    @option(
        "song",
        description='Song title, beginning lyrics, or page number in Flerstämt.',
        autocomplete=autocomplete_page
    )
    async def song(self, ctx, song: str):
        result = self.lookup.get(song, None)
        if result is None:
            result = self.by_page.get(song, None)

        if result is None:
            await ctx.respond("Jag kunde inte hitta sången du letar efter. :(")
        else:
            if 'page' in result and result['page']:
                view = SongView(self.bot, "Flerstämt", FLERSTÄMT_PDF_URL, result['tones'])
            elif 'url' in result:
                view = SongView(self.bot, "Noter", result['url'], result['tones'])
            else:
                view = None

            await ctx.respond(embeds=[self.create_embed(result)], view=view)


class SongView(discord.ui.View):
    def __init__(self, bot, link_title, url, notes, *items, **kwargs):
        super().__init__(*items, timeout=None, **kwargs)
        self.bot = bot
        self.notes = notes
        self.add_item(discord.ui.Button(label=link_title, url=url, emoji="<:pdf:1092947757498650805>"))
        if link_title == 'Flerstämt':
            self.add_item(discord.ui.Button(label="MIDI-mapp", url=FLERSTÄMT_MIDI_URL, emoji="<:drive:1092948377794252941>"))

    @discord.ui.button(label="Ta ton", style=discord.ButtonStyle.primary, emoji="<:stamgaffel:1089692591672537179>")
    async def button_callback(self, button, interaction):
        await player.play_note(interaction, self.bot, self.notes)



def setup(bot):
    bot.add_cog(Song(bot))
