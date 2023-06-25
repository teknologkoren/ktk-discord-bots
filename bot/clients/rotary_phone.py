import aiohttp
from instance.config import ROTARY_PHONE_URL

async def play_note(interaction, notes):
    async with aiohttp.ClientSession() as session:
        async with session.get(ROTARY_PHONE_URL, params={"notes": ",".join(notes)}) as response:
            response.raise_for_status()

            # Respond to the interaction to let Discord know it was successful.
            await interaction.response.edit_message()

            return await response.json()