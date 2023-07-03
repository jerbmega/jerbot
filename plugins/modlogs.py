# This plugin handles automatic logging of joins, leaves, bans, edits, and deletions.

import hikari
import lightbulb
from datetime import datetime

import main

plugin = lightbulb.Plugin("Mod Logs", include_datastore=True)
plugin.add_checks(lightbulb.human_only)


async def log_embed(
    user: str = None,
    desc: str = None,
    event: str = None,
    color: str = None,
    footer: str = None,
    fields: list = [],
):
    embed = hikari.embeds.Embed(
        title=user.username,
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


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and "member_joins" in plugin.d["config"][event.guild_id]
    ):
        account_age = event.member.joined_at.replace(
            microsecond=0
        ) - event.user.created_at.replace(microsecond=0)
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["member_joins"]["channel"]
        ).send(
            embed=await log_embed(
                user=event.user,
                event="Member joined.",
                color=plugin.d["config"][event.guild_id]["member_joins"][
                    ("new_account_color" if account_age.days <= 7 else "color")
                ],
                footer=("New account detected!" if account_age.days <= 7 else None),
                fields=[
                    {
                        "name": "Account Creation Date",
                        "value": f"<t:{round(event.user.created_at.timestamp())}:F>",
                    },
                    {"name": "User ID", "value": event.user_id},
                    {
                        "name": "Account Age",
                        "value": account_age,
                    },
                ],
            ),
        )


@plugin.listener(hikari.MemberDeleteEvent)
async def on_member_leave(event: hikari.MemberDeleteEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and "member_leaves" in plugin.d["config"][event.guild_id]
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["member_leaves"]["channel"]
        ).send(
            embed=await log_embed(
                user=event.user,
                event="Member left.",
                color=plugin.d["config"][event.guild_id]["member_leaves"]["color"],
                fields=[
                    {"name": "User ID", "value": event.user_id},
                    (
                        {"name": "Nickname", "value": event.old_member.nickname}
                        if event.old_member
                        else {
                            "name": "Nickname",
                            "value": "Unavailable",
                        }  # this prevents issues from a cache miss
                    ),
                ],
            ),
        )


@plugin.listener(hikari.GuildMessageDeleteEvent)
async def on_message_delete(event: hikari.GuildMessageDeleteEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and "message_deletes" in plugin.d["config"][event.guild_id]
        and event.old_message != None
        and event.old_message.content != None
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["message_deletes"]["channel"]
        ).send(
            embed=await log_embed(
                user=event.old_message.author,
                event="Message deleted.",
                color=plugin.d["config"][event.guild_id]["message_deletes"]["color"],
                fields=[
                    {
                        "name": "Channel",
                        "value": plugin.bot.cache.get_guild_channel(
                            event.channel_id
                        ).mention,
                    },
                    {"name": "Message", "value": event.old_message.content},
                ],
            ),
        )


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and "message_edits" in plugin.d["config"][event.guild_id]
        and not event.message.content == hikari.UNDEFINED
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["message_edits"]["channel"]
        ).send(
            embed=await log_embed(
                user=event.old_message.author,
                event="Message edited.",
                color=plugin.d["config"][event.guild_id]["message_edits"]["color"],
                fields=[
                    {
                        "name": "Channel",
                        "value": plugin.bot.cache.get_guild_channel(
                            event.channel_id
                        ).mention,
                    },
                    {"name": "Before", "value": event.old_message.content},
                    {"name": "After", "value": event.message.content},
                ],
            ),
        )


@plugin.listener(hikari.BanCreateEvent)
async def on_member_banned(event: hikari.BanCreateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and "member_bans" in plugin.d["config"][event.guild_id]
    ):
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["member_bans"]["channel"]
        ).send(
            embed=await log_embed(
                user=event.user,
                event="Member banned.",
                color=plugin.d["config"][event.guild_id]["member_bans"]["color"],
            ),
        )


def load(bot):
    bot.add_plugin(plugin)
    main.load_plugin_configs("modlogs", plugin.d)


def unload(bot):
    bot.remove_plugin(plugin)
