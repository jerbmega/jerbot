# This plugin handles extra moderation commands.

import asyncio
import hikari
import lightbulb
import datetime

import main
import db


def get_enabled_guilds():
    main.load_plugin_configs("modutil", plugin.d)
    return tuple(plugin.d["config"].keys())


plugin = lightbulb.Plugin("Mod Util", include_datastore=True)


@plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.BAN_MEMBERS))
@lightbulb.option(
    "delete_days",
    "How many days worth of messages the user sent will be deleted",
    int,
    required=False,
    min_value=0,
    max_value=7,
)
@lightbulb.option(
    "reason", "Reason the user is being unbanned", str, required=False, default=""
)
@lightbulb.option("user", "ID and discriminator of user to unban", hikari.User)
@lightbulb.command("ban", "Ban a user", guilds=get_enabled_guilds())
@lightbulb.implements(lightbulb.SlashCommand)
async def ban(ctx: lightbulb.Context) -> None:
    await ctx.get_guild().ban(
        ctx.options.user,
        reason=ctx.options.reason,
    )
    await ctx.respond("User has been banned.")


@plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.BAN_MEMBERS))
@lightbulb.option(
    "reason", "Reason the user is being unbanned", str, required=False, default=""
)
@lightbulb.option(
    "user", "ID and discriminator of user to unban", str, autocomplete=True
)
@lightbulb.command("unban", "Unban a user", guilds=get_enabled_guilds())
@lightbulb.implements(lightbulb.SlashCommand)
async def unban(ctx: lightbulb.Context) -> None:
    await ctx.get_guild().unban(
        await db.query(
            "bancache",
            f'SELECT id FROM guild_{ctx.guild_id} WHERE searchable = "{ctx.options.user}"',
        ),
        reason=ctx.options.reason,
    )
    await ctx.respond("User has been unbanned.")


@unban.autocomplete("user")
async def unban_autocomplete(option, interaction):
    # Discord doesn't support command autocomplete for users, so we have to do it this way.
    # There's some additional annoying restrictions- mainly, text autocomplete can only support up to 25 entries at a time.
    # Hopefully this SQL oneliner suffices.

    if not await db.query(
        "bancache", f"SELECT searchable FROM guild_{interaction.guild_id}"
    ):
        bans = await interaction.app.rest.fetch_bans(interaction.guild_id)
        await prepare_cache(bans, interaction.guild_id)
        return ["(Building cache... try again in a few!)"]

    return await db.queryall(
        "bancache",
        (
            f'SELECT searchable FROM guild_{interaction.guild_id} WHERE searchable LIKE "%{option.value}%" ORDER BY searchable ASC LIMIT 25'
        ),
    )


async def prepare_cache(bans, guild):
    for ban in bans:
        await db.insert(
            "bancache",
            f"guild_{guild}",
            (
                ban.user.id,
                f"{ban.user.username}#{ban.user.discriminator}",
            ),
        )


@plugin.listener(hikari.BanCreateEvent)
async def on_member_banned(event: hikari.BanCreateEvent) -> None:
    if event.guild_id in plugin.d["config"]:
        await db.insert(
            "bancache",
            f"guild_{event.guild_id}",
            (ban.user.id, f"{ban.user.username}#{ban.user.discriminator}"),
        )


@plugin.command
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.option(
    "time",
    "How many days of history to purge",
    int,
    required=False,
    min_value=1,
    max_value=14,
    default=14,
)
@lightbulb.option("user", "User to purge messages from", hikari.User, required=False)
@lightbulb.option("messages", "Amount of messages to purge", int, max_value=500)
@lightbulb.command(
    "purge", "Bulk delete messages from a channel", guilds=get_enabled_guilds()
)
@lightbulb.implements(lightbulb.SlashCommand)
async def purge(ctx: lightbulb.Context) -> None:
    print(ctx.options.user)
    limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=ctx.options.time
    )
    iterator = (
        ctx.bot.rest.fetch_messages(ctx.get_channel())
        .take_while(lambda message: (message.created_at > limit))
        .filter(
            lambda message: (message.author.id == ctx.options.user.id)
            if ctx.options.user
            else True
        )  # Direct comparisons didn't work here in my testing for some reason :person_shrugging: Maybe one's just a PartialUser?
        .limit(ctx.options.messages)
    )

    async for messages in iterator.chunk(100):
        await ctx.bot.rest.delete_messages(ctx.get_channel().id, messages)
    await ctx.respond("Purged.", flags=hikari.MessageFlag.EPHEMERAL)


def load(bot):
    bot.add_plugin(plugin)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    for guild in plugin.d["config"]:
        if (datetime.datetime.now() - bot.d["start_time"]).seconds < 10:
            if loop and loop.is_running():
                loop.create_task(
                    db.del_table("bancache")
                )  # Clear ban cache just in case something happened while the bot was offline
                loop.create_task(
                    db.create_table(
                        "bancache",
                        f"guild_{guild}",
                        ("id", "searchable"),
                    )
                )
            else:
                asyncio.run(db.del_table("bancache"))
                asyncio.run(
                    db.create_table(
                        "bancache",
                        f"guild_{guild}",
                        ("id", "searchable"),
                    )
                )


def unload(bot):
    bot.remove_plugin(plugin)
