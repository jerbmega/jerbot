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


def get_enabled_guilds():
    main.load_plugin_configs("probate", plugin.d)
    return tuple(plugin.d["config"].keys())


@lightbulb.Check
def check_authorized(context: lightbulb.Context) -> bool:
    return any(
        item in context.member.role_ids
        for item in plugin.d["config"][context.guild_id]["allowed_roles"]
    )


plugin = lightbulb.Plugin("Probate", include_datastore=True)
plugin.add_checks(lightbulb.human_only, check_authorized)


def parse_time(time_str: str):
    unit = time_str[-1:]
    time = int(time_str[:-1])
    return datetime.now() + timedelta(
        hours=time if unit == "h" else 0,
        days=time
        if unit == "d"
        else time * 30
        if unit == "m"
        else time * 365
        if unit == "y"
        else 0,
        weeks=time if unit == "w" else 0,
    )


def timestamp_to_human(
    timestamp: float,
):  # can't find a function in hikari for this but will happily replace if there is one
    return f"<t:{int(timestamp)}:F>"


def timestamp_to_human_eta(
    timestamp: float,
):
    return f"<t:{int(timestamp)}:R>"


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


async def strike_dm_embed(content: str = None, guild_id: int = None):
    guild = plugin.bot.cache.get_guild(guild_id)
    embed = hikari.embeds.Embed(color=plugin.d["config"][guild_id]["dm_color"])
    embed.set_author(name=content)
    embed.set_footer(text=guild.name, icon=guild.icon_url)
    return embed


async def probate_user(
    guild: hikari.Guild,
    user: hikari.User,
    reason: str,
    time: datetime,
):
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
            hikari.PermissionOverwrite(
                id=user.id,
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
            topic=f"{user.mention} - {time}{(' - ' + reason) if reason else ''}",
            category=category,
            permission_overwrites=overwrites,
        )
    elif reason:
        await channel.edit(
            topic=f"{user.mention} - {time} - {reason}",
        )
    await db.insert(
        "probate",
        f"probations_{guild.id}",
        "(?,?,?,?)",
        (user.id, channel.id, time, reason),
    )
    await db.create_table(
        "probate", f"logs_{user.id}", ("author", "username", "content", "time")
    )
    await channel.send(
        content=plugin.d["config"][guild.id]["info_message"]
        .replace("%mention%", user.mention)
        .replace("%time%", timestamp_to_human_eta(parse_time(time).timestamp()))
    )
    scheduler.add_job(
        unprobate_user,
        DateTrigger(parse_time(time)),
        id=f"unprobate_{guild.id}_{user.id}",
        replace_existing=True,
        args=(guild.id, user.id),
    )


async def unprobate_user(guild_id: int, user_id: int, user_leave: bool = False):
    if not user_leave:
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

    try:
        await (
            await plugin.bot.rest.fetch_user(user_id)
        ).send(  # highly doubt the cache will be populated on early load
            content=plugin.d["config"][guild_id]["unprobation_message"]
        )
    except hikari.errors.ForbiddenError:
        pass

    if not user_leave:
        await db.remove("probate", f"probations_{guild_id}", f"user_id = {user_id}")
    if "log_channel" in plugin.d["config"][guild_id]:
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
                event="Probation deleted (user left)."
                if user_leave
                else "Probation expired.",
                desc="The probation will be automatically reinstated upon next user join."
                if user_leave
                else None,
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
    try:
        await ctx.options.user.send(
            plugin.d["config"][ctx.guild_id]["probation_message"].replace(
                "%time%", timestamp_to_human(parse_time(ctx.options.time).timestamp())
            )
        )
    except hikari.errors.ForbiddenError:
        pass
    if "log_channel" in plugin.d["config"][ctx.guild_id]:
        embed = await log_embed(
            user=ctx.options.user,
            event="User placed in probation.",
            desc=f"An archive of the probation chat will be available once the probation expires.",
            color=plugin.d["config"][ctx.guild_id]["log_color"],
            fields=[
                {"name": "User ID", "value": ctx.options.user.id},
                {
                    "name": "Scheduled Release Time",
                    "value": timestamp_to_human(
                        parse_time(ctx.options.time).timestamp()
                    ),
                },
                {
                    "name": "Issuer",
                    "value": f"{ctx.author.username}#{ctx.author.discriminator}",
                },
            ],
        )

        if ctx.options.reason:
            embed.add_field("Reason", ctx.options.reason)

        await ctx.bot.cache.get_guild_channel(
            plugin.d["config"][ctx.guild_id]["log_channel"]
        ).send(embed=embed)
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


@plugin.command
@lightbulb.option(
    "time",
    "Amount of time before the strike expires. Leave blank to make the strike permanent.",
    str,
    required=False,
)
@lightbulb.option(
    "reason",
    "Reason for striking. Optional, highly recommended.",
    str,
    required=False,
    default="No reason provided.",
)
@lightbulb.option(
    "user",
    "User to strike",
    hikari.User,
)
@lightbulb.command(
    "strike",
    "Strike a user",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def strike(ctx: lightbulb.Context) -> None:
    if ctx.options.user.is_bot:
        raise err.UnstrikeableBot

    for role in ctx.get_guild().get_member(ctx.options.user).role_ids:
        if role in plugin.d["config"][ctx.guild_id]["allowed_roles"]:
            raise err.UnstrikeableRole

    if ctx.options.time:
        scheduled_time = parse_time(ctx.options.time)
        scheduled_timestamp_round = int(scheduled_time.timestamp())
    await db.insert(
        "probate",
        f"strikes_{ctx.guild_id}",
        "(?,?,?)",
        (
            ctx.options.user.id,
            ctx.options.reason,
            scheduled_timestamp_round if ctx.options.time else None,
        ),
    )
    strike_num = len(
        await db.queryall(
            "probate",
            f"select id from strikes_{ctx.guild_id} where id = {ctx.options.user.id}",
        )
    )

    try:
        response = "temp_strike_message" if ctx.options.time else "strike_message"
        response = (
            plugin.d["config"][ctx.guild_id][response]
            .replace("%time%", timestamp_to_human(parse_time("24h").timestamp()))
            .replace("%num_strikes%", str(strike_num))
        )
        if ctx.options.time:
            response = response.replace(
                "%expiry_time%",
                timestamp_to_human(scheduled_time.timestamp()),
            )
        await ctx.options.user.send(
            response,
            embed=await strike_dm_embed(ctx.options.reason, ctx.guild_id),
        )
    except (hikari.errors.ForbiddenError, hikari.errors.BadRequestError):
        pass

    if ctx.options.time:
        scheduler.add_job(
            db.remove,
            DateTrigger(scheduled_time),
            id=f"delstrike_{ctx.guild_id}_{ctx.options.user.id}_{scheduled_timestamp_round}",
            replace_existing=True,
            args=(
                "probate",
                f"strikes_{ctx.guild_id}",
                f"timestamp = {scheduled_timestamp_round} limit 1",
            ),
        )

    if "log_channel" in plugin.d["config"][ctx.guild_id]:

        embed = await log_embed(
            user=ctx.options.user,
            event=f"Strike issued (strike {strike_num}).",
            color=plugin.d["config"][ctx.guild_id]["log_color"],
            fields=[
                {"name": "User ID", "value": ctx.options.user.id},
                {
                    "name": "Issuer",
                    "value": f"{ctx.author.username}#{ctx.author.discriminator}",
                },
            ],
        )

        if ctx.options.time:
            embed.add_field(
                "Scheduled Expiry Time",
                timestamp_to_human(scheduled_time.timestamp()),
                inline=True,
            )

        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][ctx.guild_id]["log_channel"]
        ).send(embed=embed)

    await probate_user(ctx.get_guild(), ctx.options.user, ctx.options.reason, "24h")
    if (
        plugin.d["config"][ctx.guild_id]["strikes_ban_on"]
        and strike_num >= plugin.d["config"][ctx.guild_id]["strikes_ban_on"]
    ):
        await ctx.get_guild().ban(
            ctx.options.user, reason=f"Strike {strike_num} (automatic ban)."
        )
    elif (
        plugin.d["config"][ctx.guild_id]["strikes_kick_on"]
        and strike_num >= plugin.d["config"][ctx.guild_id]["strikes_kick_on"]
    ):
        await ctx.get_guild().kick(
            ctx.options.user, reason=f"Strike {strike_num} (automatic kick)."
        )
    await ctx.respond(f"Done. This is strike {strike_num}.")


@plugin.command
@lightbulb.option(
    "user",
    "User to list strikes for",
    hikari.User,
)
@lightbulb.command(
    "liststrikes",
    "List all strikes a user has",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def liststrikes(ctx: lightbulb.Context) -> None:
    strikes = await db.queryall(
        "probate",
        f"select reason from strikes_{ctx.guild_id} where id = {ctx.options.user.id}",
    )
    if not strikes:
        raise err.UserHasNoStrikes
    embed = hikari.embeds.Embed(
        title=f"{ctx.options.user.username}#{ctx.options.user.discriminator}",
        color=plugin.d["config"][ctx.guild_id]["log_color"],
    )
    for i, strike in enumerate(strikes, 1):
        embed.add_field(f"Strike {i}", strike)
    await ctx.respond(embed=embed)


@plugin.command
@lightbulb.option(
    "reason",
    "Reason of the strike to remove (this will autocomplete)",
    autocomplete=True,
)
@lightbulb.option(
    "user",
    "User to remove a strike from",
    hikari.User,
)
@lightbulb.command(
    "delstrike",
    "Delete a strike from a user's record",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def delstrike(ctx: lightbulb.Context) -> None:
    strike_time = await db.query(
        "probate",
        f'select timestamp from strikes_{ctx.guild_id} where id == {ctx.options.user.id} and reason == "{ctx.options.reason}" limit 1',
    )

    await db.remove(
        "probate",
        f"strikes_{ctx.guild_id}",
        f'id == {ctx.options.user.id} and reason == "{ctx.options.reason}" limit 1',
    )
    if strike_time:
        scheduler.remove_job(
            f"delstrike_{ctx.guild_id}_{ctx.options.user.id}_{strike_time}"
        )

    try:
        new_strike_num = len(
            await db.queryall(
                "probate",
                f"select id from strikes_{ctx.guild_id} where id = {ctx.options.user.id}",
            )
        )
    except TypeError:
        new_strike_num = 0

    await ctx.respond(f"Done. User now has {new_strike_num} strikes.")


@delstrike.autocomplete("reason")
async def delstrike_autocomplete(option, interaction):
    user_id = interaction.options[0].value
    return await db.queryall(
        "probate",
        (
            f'SELECT reason FROM strikes_{interaction.guild_id} WHERE reason LIKE "%{option.value}%" AND id == {user_id} LIMIT 25'
        ),
    )


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    await log_message(event)


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    await log_message(event)


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    if event.guild_id in plugin.d["config"] and event.user.id == await db.query(
        "probate",
        f"select user_id from probations_{event.guild_id} where user_id = {event.user.id}",
    ):

        old_data = await db.query(
            "probate",
            f"select time, reason from probations_{event.guild_id} where user_id = {event.user.id}",
        )
        await probate_user(
            event.get_guild(),
            event.user,
            f"Reinstated from a previous probation - {old_data[1]}",
            old_data[0],
        )

        if "log_channel" in plugin.d["config"][event.guild_id]:
            await plugin.bot.cache.get_guild_channel(
                plugin.d["config"][event.guild_id]["log_channel"]
            ).send(
                embed=await log_embed(
                    user=event.user,
                    event="User placed in probation.",
                    desc=f"A previously created probation has been automatically reinstated upon user rejoin. The probation timer has been reset.\nAn archive of the probation chat will be available once the probation expires.",
                    color=plugin.d["config"][event.guild_id]["log_color"],
                    fields=[
                        {"name": "User ID", "value": event.user.id},
                        {
                            "name": "Scheduled Release Time",
                            "value": timestamp_to_human(
                                parse_time(old_data[0]).timestamp()
                            ),
                        },
                    ],
                ),
            )


@plugin.listener(hikari.MemberDeleteEvent)
async def on_member_leave(event: hikari.MemberDeleteEvent) -> None:
    if event.guild_id in plugin.d["config"] and event.user.id == await db.query(
        "probate",
        f"select user_id from probations_{event.guild_id} where user_id = {event.user.id}",
    ):
        await unprobate_user(event.guild_id, event.user.id, True)
        await scheduler.remove_job(f"unprobate_{event.guild_id}_{event.user.id}")


def load(bot):
    bot.add_plugin(plugin)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    for guild in plugin.d["config"]:
        if loop and loop.is_running():
            loop.create_task(
                db.create_table(
                    "probate",
                    f"probations_{guild}",
                    ("user_id", "channel_id", "time", "reason"),
                )
            )
            loop.create_task(
                db.create_table(
                    "probate", f"strikes_{guild}", ("id", "reason", "timestamp")
                )
            )
        else:
            asyncio.run(
                db.create_table(
                    "probate",
                    f"probations_{guild}",
                    ("user_id", "channel_id", "time", "reason"),
                )
            )
            asyncio.run(
                db.create_table(
                    "probate", f"strikes_{guild}", ("id", "reason", "timestamp")
                )
            )


def unload(bot):
    bot.remove_plugin(plugin)
