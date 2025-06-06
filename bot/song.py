import json
import re
import sys
import unicodedata

import discord
from discord import commands, option

from instance.config import DISCORD_SINE_EMOJI_ID, DISCORD_ISAK_EMOJI_ID, ROTARY_PHONE_URL


def clean_string(s):
    s = s.lower()
    # Do some unicode normalization.
    s = unicodedata.normalize('NFKD', s)
    # Remove all characters except alphanumeric and spaces
    s = re.sub(r'[^a-zA-Z0-9\s]', '', s)
    # Replace multiple spaces with a single space
    s = re.sub(r'\s+', ' ', s)
    # Strip leading/trailing whitespace
    return s.strip()


class Song(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("instance/songs.json", "r") as f:
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
                   if not ctx.value or clean_string(key).startswith(clean_string(ctx.value))]

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
            # Send response message.
            embed = self.create_embed(result)
            view = self.create_song_view(result)
            await ctx.send_response(embeds=[embed], view=view)

            # Drink of the week sheet music
            if result['name'] == "Veckans drink":
                with open("images/veckans_drink_2023-04-16.png", "rb") as fp:
                    await ctx.channel.send(file=discord.File(fp))

            # Easter egg
            if result['name'] == "Die Beredsamkeit" and ctx.user.id == 242287639334617090:
                with open("images/die_beredsamkeit.jpg", "rb") as fp:
                    await ctx.channel.send(file=discord.File(fp))

            # Add reactions to select sound.
            vote = None
            async for message in ctx.channel.history():
                if not message.embeds:
                    continue
                if message.embeds[0].title == embed.title:
                    vote = message
                    break

            if vote is None:
                print("Could not find the song message just sent.", file=sys.stderr)
            else:
                await vote.add_reaction(f"<:sine:{DISCORD_SINE_EMOJI_ID}>")
                await vote.add_reaction(f"<:isak:{DISCORD_ISAK_EMOJI_ID}>")

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
            row=0,
        ))

        if ROTARY_PHONE_URL is not None:
            view.add_item(discord.ui.Button(
                emoji="☎",
                label="Ring Sqrubben",
                style=discord.ButtonStyle.green,
                custom_id=f"call-{song['id']}",
                row=0,
            ))

        for link in song.get('links', ()):
            emoji = None
            row = 2
            if link[0].startswith('Not'):
                emoji = '<:pdf:1092947757498650805>'
                row = 0
            elif link[0].startswith('MIDI'):
                emoji = '🎹'
                row = 1
            elif link[0] == 'Sibelius':
                emoji = '🎶'
                row = 0
            elif link[0] == 'Repfiler':
                emoji = "<:drive:1092948377794252941>"
                row = 0

            view.add_item(discord.ui.Button(
                emoji=emoji,
                label=link[0],
                url=link[1],
                row=row
            ))
            
        return view


def setup(bot):
    bot.add_cog(Song(bot))
