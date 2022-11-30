# This plugin handles user strikes and probations.

import hikari
import lightbulb
import asyncio
import os
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


async def log_embed(
    user: str = None,
    desc: str = None,
    event: str = None,
    color: str = None,
    footer: str = None,
    fields: list = [],
):
    embed = hikari.embeds.Embed(
        title=f"{user.username}#{user.discriminator}",
        description=desc,
        color=color,
        timestamp=datetime.now().astimezone(),
    )
    embed.set_author(name=event)
    embed.set_footer(text=footer)
    embed.set_thumbnail(user.avatar_url)

    for field in fields:
        embed.add_field(field["name"], field["value"], inline=True)
    return embed


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
    elif reason:
        await channel.edit(
            topic=f"{user.mention}{(' - ' + reason)}",
        )
    await db.insert("probate", f"probations_{guild.id}", (user.id, channel.id))
    await db.create_table(
        "probate", f"logs_{user.id}", ("author", "username", "content", "time")
    )
    await channel.send(content=plugin.d["config"][guild.id]["info_message"])
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

    await db.remove("probate", f"probations_{guild_id}", f"user_id = {user_id}")
    if plugin.d["config"][guild_id]["log_channel"]:
        with open(f"/tmp/logs_{user_id}.txt", "w+") as logs:  # TODO async this?
            for message in await db.queryall(
                "probate", f"select * from logs_{user_id}"
            ):
                logs.write(
                    f"[{message[3]} UTC] <{message[1]} ({message[0]})> - {message[2]}\n"
                )
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][guild_id]["log_channel"]
        ).send(
            embed=await log_embed(
                user=await plugin.bot.rest.fetch_user(user_id),
                event="Probation expired.",
                color=plugin.d["config"][guild_id]["log_color"],
                fields=[
                    {"name": "User ID", "value": user_id},
                ],
            ),
            attachment=f"/tmp/logs_{user_id}.txt",
        )
    os.remove(f"/tmp/logs_{user_id}.txt")
    await db.drop_table("probate", f"logs_{user_id}")


async def log_message(event: hikari.Event):
    if (
        event.guild_id in plugin.d["config"]
        and not event.message.content == hikari.UNDEFINED
    ):
        user_id = await db.query(
            "probate",
            f"select user_id from probations_{event.guild_id} where channel_id = {event.channel_id}",
        )
        if user_id:
            await db.insert(
                "probate",
                f"logs_{user_id}",
                "(?,?,?,?)",
                (
                    event.author_id,
                    event.message.author.username,
                    event.message.content,
                    datetime.utcnow(),
                ),
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
    if plugin.d["config"][ctx.guild_id]["log_channel"]:
        await ctx.bot.cache.get_guild_channel(
            plugin.d["config"][ctx.guild_id]["log_channel"]
        ).send(
            embed=await log_embed(
                user=ctx.options.user,
                event="User placed in probation.",
                desc=f"**{ctx.author.username}#{ctx.author.discriminator}{(' - ' + ctx.options.reason) if ctx.options.reason else ''}**\nAn archive of the probation chat will be available once the probation expires.",
                color=plugin.d["config"][ctx.guild_id]["log_color"],
                fields=[
                    {"name": "User ID", "value": ctx.options.user.id},
                    {
                        "name": "Scheduled Release Time",
                        "value": timestamp_to_human(
                            parse_time(ctx.options.time).timestamp()
                        ),
                    },
                ],
            ),
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
        f"select user_id from probations_{ctx.guild_id} where user_id = {ctx.options.user.id}",
    ):
        raise err.UserNotInProbation
    await unprobate_user(ctx.guild_id, ctx.options.user.id)
    scheduler.remove_job(f"unprobate_{ctx.guild_id}_{ctx.options.user.id}")
    await ctx.respond("Done.")


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    await log_message(event)


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    await log_message(event)


def load(bot):
    bot.add_plugin(plugin)
    plugin.d["bot"] = bot
    for guild in plugin.d["config"]:
        asyncio.run(
            db.create_table("probate", f"probations_{guild}", ("user_id", "channel_id"))
        )
        asyncio.run(db.create_table("probate", f"strikes_{guild}", ("id", "reason")))


def unload(bot):
    bot.remove_plugin(plugin)
