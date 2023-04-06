import sys
from config import DISCORD_VIP_ROLE_ID, DISCORD_VIP_CHANNEL_ID

import streque
from group_config import ROLES


async def set_extra_roles(member, bot):
    streque_user = await streque.get_user_by_discord(member.id)
    name = streque_user['full_name']

    to_add = []
    for role_id, members in ROLES.items():
        if name in members:
            role = member.guild.get_role(role_id)
            to_add.append(role)

    if streque_user['balance'] > 1000_00:
        role = member.guild.get_role(DISCORD_VIP_ROLE_ID)
        to_add.append(role)

    await member.add_roles(*to_add)
    print(f"Added {name} to the roles: {to_add}", file=sys.stderr)

    if streque_user['balance'] > 1000_00:
        channel = await member.guild.fetch_channel(DISCORD_VIP_CHANNEL_ID)
        await channel.send(f"<@{member.id}> Välkommen till VIP-loungen på Discord! :partying_face:")
