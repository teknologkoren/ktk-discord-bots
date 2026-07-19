# Tests for bot/club.py: the permission guards on the /club add command.
from unittest.mock import AsyncMock, MagicMock

import bot.club as club


def make_cog():
    return club.Club(MagicMock(name='bot'))


async def test_add_outside_guild_responds_with_error():
    cog = make_cog()
    ctx = MagicMock(name='ctx')
    ctx.guild = None
    ctx.respond = AsyncMock()

    await club.Club.add.callback(cog, ctx, '🎲', 'Spelklubben', 'spel', 'Vi spelar spel.')

    ctx.respond.assert_awaited_once_with(
        'Detta kommando kan endast användas från en server-kanal.')


async def test_add_without_manage_guild_responds_with_error():
    cog = make_cog()
    ctx = MagicMock(name='ctx')
    ctx.respond = AsyncMock()
    ctx.user.guild_permissions.manage_guild = False

    await club.Club.add.callback(cog, ctx, '🎲', 'Spelklubben', 'spel', 'Vi spelar spel.')

    ctx.respond.assert_awaited_once_with(
        'Du har ej behörighet att köra detta kommando, vänligen be en admin att hjälpa dig.')
    ctx.guild.create_role.assert_not_called()
