# This plugin handles owner-only commands intended to strenghten the safety of every opted-in server- lovingly dubbed AEGIS.

import hikari
import lightbulb
import asyncio
import aiohttp
import re

import main
import db
import err


def get_enabled_guilds():
    main.load_plugin_configs("aegis", plugin.d)
    return tuple(plugin.d["config"].keys())


plugin = lightbulb.Plugin("AEGIS", include_datastore=True)
plugin.add_checks(lightbulb.owner_only)


@plugin.command
@lightbulb.option(
    "users",
    "Hyperlink to a raw list of user ID's to ban across every opted-in server",
    str,
)
@lightbulb.command(
    "global_ban",
    "Globally bans a list of user ID's across every opted-in server",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def global_ban(ctx: lightbulb.Context) -> None:
    users = None
    eligible_guilds = []

    for guild in get_enabled_guilds():
        if "global_ban" in plugin.d["config"][guild]:
            eligible_guilds.append(guild)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ctx.options.users) as response:
                response = await response.text()
                if re.search("[a-zA-Z]", response):
                    raise err.NonAlphanumericGlobalBanException
                users = response.split(" ")
    except aiohttp.client_exceptions.InvalidURL:
        raise err.InvalidGlobalBanURL

    await ctx.respond(
        f"Processing {len(users)} users across {len(elegible_guilds)} servers. Buckle up... this is gonna take a while.",
        flags=hikari.MessageFlag.EPHEMERAL,
    )

    for guild in eligible_guilds:
        guild = ctx.bot.cache.get_guild(guild)
        for user in users:
            try:
                await guild.ban(user)
                await asyncio.sleep(1)
            except hikari.errors.NotFoundError:
                pass
    await ctx.edit_last_response("Done.")


@plugin.command
@lightbulb.option(
    "announcement",
    "Announcement to send to every opted-in server",
    str,
)
@lightbulb.command(
    "announce",
    "Sends an announcement to every opted-in server",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def announce(ctx: lightbulb.Context) -> None:
    eligible_guilds = []

    for guild in get_enabled_guilds():
        if "announcements" in plugin.d["config"][guild]:
            eligible_guilds.append(guild)

    await ctx.respond(
        f"Sending announcement to {len(eligible_guilds)} servers.",
        flags=hikari.MessageFlag.EPHEMERAL,
    )

    for guild in eligible_guilds:
        try:
            await plugin.bot.cache.get_guild_channel(
                plugin.d["config"][guild]["announcements"]["channel"]
            ).send(ctx.options.announcement)
        except hikari.errors.ForbiddenError:
            pass

    await ctx.edit_last_response("Done.")


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
