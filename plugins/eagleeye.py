# This plugin handles automatic forwarding of messages sent by select users to a log channel.

import hikari
import lightbulb
import asyncio
from datetime import datetime

import main
import db


def get_enabled_guilds():
    main.load_plugin_configs("watchlist", plugin.d)
    return tuple(plugin.d["config"].keys())


@lightbulb.Check
def check_authorized(context: lightbulb.Context) -> bool:
    return any(
        item in context.member.role_ids
        for item in plugin.d["config"][context.guild_id]["roles"]
    )


plugin = lightbulb.Plugin("Watchlist", include_datastore=True)
plugin.add_checks(lightbulb.human_only, check_authorized)


@plugin.command
@lightbulb.option("reason", "Reason for adding user to the watchlist")
@lightbulb.option("user", "User to watch", hikari.User)
@lightbulb.command("watch", "Add a user to the watchlist", guilds=get_enabled_guilds())
@lightbulb.implements(lightbulb.SlashCommand)
async def watch(ctx: lightbulb.Context) -> None:
    await db.insert(
        "watchlist",
        f"guild_{ctx.guild_id}",
        (ctx.options.user.id, ctx.options.reason),
    )
    await ctx.respond(f"`{ctx.options.user.username}` added to the watchlist.")


@plugin.command
@lightbulb.option(
    "user", "User to remove", hikari.User
)  # there is no way of getting a list of people in the db cleanly here because we have multiple guilds :(
@lightbulb.command(
    "unwatch", "Remove a user from the watchlist", guilds=get_enabled_guilds()
)
@lightbulb.implements(lightbulb.SlashCommand)
async def unwatch(ctx: lightbulb.Context) -> None:
    await db.remove("watchlist", f"guild_{ctx.guild_id}", f"id = {ctx.options.user.id}")
    await ctx.respond(f"`{ctx.options.user.username}` removed from the watchlist.")


async def watchlist_embed(
    message: hikari.Message = None,
    guild_id: int = None,
    user: hikari.User = None,
    channel: hikari.GuildChannel = None,
):
    embed = hikari.embeds.Embed(
        title=f"{user.username}#{user.discriminator} ({user.id})",
        description=f"[#{channel.name}](https://discordapp.com/channels/{message.guild_id}/{channel.id}/{message.id})",
        color=plugin.d["config"][guild_id]["log_color"],
        timestamp=datetime.now().astimezone(),
    )
    embed.set_author(name="Message created.")
    embed.set_thumbnail(user.avatar_url)
    embed.add_field(name="Message content", value=message.content, inline=True)
    return embed


async def watchlist_embed_edit(
    old_message: hikari.Message = None,
    message: hikari.Message = None,
    guild_id: int = None,
    user: hikari.User = None,
    channel: hikari.GuildChannel = None,
):
    embed = hikari.embeds.Embed(
        title=f"{user.username}#{user.discriminator} ({user.id})",
        description=f"[#{channel.name}](https://discordapp.com/channels/{message.guild_id}/{channel.id}/{message.id})",
        color=plugin.d["config"][guild_id]["log_color"],
        timestamp=datetime.now().astimezone(),
    )
    embed.set_author(name="Message edited.")
    embed.set_thumbnail(user.avatar_url)
    embed.add_field(name="Old message", value=old_message.content, inline=True)
    embed.add_field(name="New message", value=message.content, inline=True)
    return embed


"""
            fields = [['Message content', message.content]]
            for attachment in message.attachments:
                fields.append(['Attachment', attachment.proxy_url])

            await write_embed(server['eagleeye']['channel'], message.author, server['eagleeye']['embed_color'],
                              f'{message.author.name} ({message.author.id})',
                              description=f'[#{message.channel.name}]'
                                          f'(https://discordapp.com/channels/{message.guild.id}/{message.channel.id}'
                                          f'/{message.id})',
                              fields=fields)
                              """


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    watched_ids = await db.queryall(
        "watchlist", f"select id from guild_{event.guild_id}"
    )
    if (
        event.guild_id in plugin.d["config"]
        and not event.content == None
        and not event.is_bot
        and watched_ids
        and event.author.id in watched_ids
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["channel"]
        ).send(
            embed=await watchlist_embed(
                message=event.message,
                guild_id=event.guild_id,
                user=event.author,
                channel=plugin.bot.cache.get_guild_channel(event.channel_id),
            )
        )


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    watched_ids = await db.queryall(
        "watchlist", f"select id from guild_{event.guild_id}"
    )
    if (
        event.guild_id in plugin.d["config"]
        and not event.content == None
        and not event.is_bot
        and watched_ids
        and event.author.id in watched_ids
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["channel"]
        ).send(
            embed=await watchlist_embed_edit(
                old_message=event.old_message,
                message=event.message,
                guild_id=event.guild_id,
                user=event.author,
                channel=plugin.bot.cache.get_guild_channel(event.channel_id),
            )
        )


def load(bot):
    bot.add_plugin(plugin)
    for guild in plugin.d["config"]:
        asyncio.run(
            db.create_table("watchlist", f"guild_{guild}", ("id", "reason"))
        )  # sqlite doesn't support db names just being numbers apparently (lame)


def unload(bot):
    bot.remove_plugin(plugin)
