import aiohttp
from instance.config import ROTARY_PHONE_URL

async def play_note(interaction, notes):
    async with aiohttp.ClientSession() as session:
        async with session.get(ROTARY_PHONE_URL, params={"notes": ",".join(notes)}) as response:
            if not response.ok:
                await interaction.response.send_message(
                    content="Oops, telefonen gav ett fel tillbaka... Prata med Anton så kan han lösa problemet.",
                    ephemeral=True
                )
                return

            res = await response.json()
            if res['status'] == 'ok':
                # Respond to the interaction to let Discord know it was successful.
                await interaction.response.edit_message()
            elif res['status'] == 'busy':
                await interaction.response.send_message(
                    content="Telefonen är upptagen. Var vänlig försök igen senare.",
                    ephemeral=True
                )
            elif res['status'] == 'malformed':
                await interaction.response.send_message(
                    content="Oj, något gick lite snett där! Prata med Anton så kan han lösa problemet.",
                    ephemeral=True
                )
