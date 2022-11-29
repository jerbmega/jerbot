# This plugin handles user strikes and probations.

import hikari
import lightbulb
import asyncio
from datetime import datetime, timedelta
from apscheduler.triggers.date import DateTrigger

import main
import db
import err
from scheduler import scheduler


plugin = lightbulb.Plugin("Probate", include_datastore=True)


def get_enabled_guilds():
    main.load_plugin_configs("probate", plugin.d)
    return tuple(plugin.d["config"].keys())


def parse_time(time_str: str):
    unit = time_str[-1:]
    time = int(time_str[:-1])
    return datetime.now() + timedelta(
        hours=time if unit == "h" else 0,
        days=time if unit == "d" else time * 30 if unit == "m" else 0,
        weeks=time if unit == "w" else time * 52 if unit == "y" else 0,
    )


def timestamp_to_human(
    timestamp: float,
):  # can't find a function in hikari for this but will happily replace if there is one
    return f"<t:{int(timestamp)}:F>"


def find_channel(guild: hikari.Guild, type: hikari.ChannelType, name: str):
    for channel in guild.get_channels().values():
        if channel.type == type and channel.name == name:
            return channel


async def probate_user(guild, user, reason, time):
    await plugin.bot.rest.add_role_to_member(
        guild.id,
        user,
        plugin.d["config"][guild.id]["probation_role"],
    )

    category = find_channel(guild, hikari.ChannelType.GUILD_CATEGORY, "Probations")

    if not category:
        category = await plugin.bot.rest.create_guild_category(
            guild.id,
            name=f"Probations",
            permission_overwrites=[
                hikari.PermissionOverwrite(
                    id=guild.id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    deny=(hikari.Permissions.VIEW_CHANNEL),
                )
            ],
        )

    channel = find_channel(
        guild,
        hikari.ChannelType.GUILD_TEXT,
        f"probation_{user.id}",
    )

    if not channel:
        overwrites = [
            hikari.PermissionOverwrite(
                id=guild.id,
                type=hikari.PermissionOverwriteType.ROLE,
                deny=(hikari.Permissions.VIEW_CHANNEL),
            ),
            hikari.PermissionOverwrite(
                id=plugin.bot.get_me().id,
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(hikari.Permissions.VIEW_CHANNEL),
            ),
        ]

        for role in plugin.d["config"][guild.id]["allowed_roles"]:
            overwrites.append(
                hikari.PermissionOverwrite(
                    id=role,
                    type=hikari.PermissionOverwriteType.ROLE,
                    allow=(hikari.Permissions.VIEW_CHANNEL),
                )
            )

        channel = await guild.create_text_channel(
            name=f"probation_{user.id}",
            topic=f"{user.mention}{(' - ' + reason) if reason else ''}",
            category=category,
            permission_overwrites=overwrites,
        )

        await channel.send(content=plugin.d["config"][guild.id]["info_message"])
    elif reason:
        await channel.edit(
            topic=f"{user.mention}{(' - ' + reason)}",
        )
    test = scheduler.add_job(
        unprobate_user,
        DateTrigger(parse_time(time)),
        id=f"unprobate_{guild.id}_{user.id}",
        replace_existing=True,
        args=(guild.id, user.id),
    )


async def unprobate_user(guild_id: int, user_id: int):
    await plugin.bot.rest.remove_role_from_member(
        guild_id,
        user_id,
        plugin.d["config"][guild_id]["probation_role"],
    )

    channel = find_channel(
        plugin.bot.cache.get_guild(guild_id),
        hikari.ChannelType.GUILD_TEXT,
        f"probation_{user_id}",
    )

    if channel:  # failsafe :person_shrugging:
        await channel.delete()

    await (
        await plugin.bot.rest.fetch_user(user_id)
    ).send(  # highly doubt the cache will be populated on early load
        content=plugin.d["config"][guild_id]["unprobation_message"]
    )


@plugin.command
@lightbulb.option(
    "time",
    "Amount of time to probate for (ex: 24h, 4d, 1w, 6m, 1y). Defaults to 1d.",
    str,
    required=False,
    default="1d",
)
@lightbulb.option(
    "reason",
    "Reason for probation",
    str,
    required=False,
)
@lightbulb.option(
    "user",
    "User to probate",
    hikari.User,
)
@lightbulb.command(
    "probate",
    "Probate a user.",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def probate(ctx: lightbulb.Context) -> None:
    await probate_user(
        ctx.get_guild(), ctx.options.user, ctx.options.reason, ctx.options.time
    )
    await ctx.options.user.send(
        plugin.d["config"][ctx.guild_id]["probation_message"].replace(
            "%time%", timestamp_to_human(parse_time(ctx.options.time).timestamp())
        )
    )
    await ctx.respond(
        f"Done. Scheduled release for {timestamp_to_human(parse_time(ctx.options.time).timestamp())}"
    )


@plugin.command
@lightbulb.option(
    "user",
    "User to prematurely unprobate",
    hikari.User,
)
@lightbulb.command(
    "unprobate",
    "Prematurely unprobate a user",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def unprobate(ctx: lightbulb.Context) -> None:
    if not await db.query(
        "probate",
        f"select id from probations_{ctx.guild_id} where id = {ctx.options.user.id}",
    ):
        raise err.UserNotInProbation
    await unprobate_user(ctx.guild_id, ctx.options.user.id)
    scheduler.remove_job(f"unprobate_{ctx.guild_id}_{ctx.options.user.id}")
    await ctx.respond("Done.")


def load(bot):
    bot.add_plugin(plugin)
    plugin.d["bot"] = bot
    for guild in plugin.d["config"]:
        asyncio.run(
            db.create_table("probate", f"probations_{guild}", ("id", "reason", "logs"))
        )
        asyncio.run(db.create_table("probate", f"strikes_{guild}", ("id", "reason")))


def unload(bot):
    bot.remove_plugin(plugin)
