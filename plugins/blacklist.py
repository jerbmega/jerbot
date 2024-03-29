# This plugin handles parsing and deleting of blacklisted words or phrases.

import re
import hikari
import lightbulb
import wordninja

from thefuzz import utils
from thefuzz.fuzz import token_sort_ratio
from thefuzz.process import extractOne
from datetime import datetime
import decancer_py as decancer

import main


plugin = lightbulb.Plugin("Blacklist", include_datastore=True)
plugin.add_checks(lightbulb.human_only)


async def log_embed(
    content: str = None,
    guild_id: int = None,
    user: hikari.User = None,
    channel: hikari.GuildChannel = None,
):
    embed = hikari.embeds.Embed(
        title="Filter tripped (automatically deleted).",
        color=plugin.d["config"][guild_id]["log_color"],
        timestamp=datetime.now().astimezone(),
    )
    embed.set_thumbnail(user.avatar_url)
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Message", value=content, inline=True)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    return embed


async def dm_embed(content: str = None, guild_id: int = None):
    guild = plugin.bot.cache.get_guild(guild_id)
    embed = hikari.embeds.Embed(color=plugin.d["config"][guild_id]["dm_color"])
    embed.set_author(name=content)
    embed.set_footer(text=guild.name, icon=guild.icon_url)
    return embed


async def is_blacklisted(message: hikari.Message):
    if "exempt_roles" in plugin.d["config"][message.guild_id]:
        for role in message.member.role_ids:
            if role in plugin.d["config"][message.guild_id]["exempt_roles"]:
                return False

    # Perform preliminary filtration with decancer, remove whitespace from the entire sentence, reconstruct it into words with wordninja
    # This avoids any attempts to dodge the filter via whitespace or unicode variation
    if "content" in plugin.d["config"][message.guild_id]:
        content = re.sub(
            r"[^a-zA-Z0-9]",
            "",
            decancer.parse(message.content),
            flags=re.UNICODE,
        )
        content = wordninja.split(content)
        for word in content:
            if utils.full_process(word):
                match = extractOne(
                    word,
                    plugin.d["config"][message.guild_id]["triggers"],
                    scorer=token_sort_ratio,
                )
                if match[1] >= 90:
                    return True

    # Try a standard blacklist next, works for filtering copypastas, Discord invites and such
    if "special_triggers" in plugin.d["config"][message.guild_id]:
        for trigger in plugin.d["config"][message.guild_id]["special_triggers"]:
            if trigger.lower() in re.sub(
                r"\s+",
                "",
                message.content.lower(),
                flags=re.UNICODE,
            ):
                return True
    return False


async def check_blacklist(event: hikari.Event):
    if await is_blacklisted(event.message):
        await event.message.delete()
        await event.author.send(
            "Your recent message has tripped the word filter and has been deleted. \nIf you believe this was done in error, contact the moderation team in the server below for more information.",
            embed=await dm_embed(content=event.content, guild_id=event.guild_id),
        )
        await plugin.bot.cache.get_guild_channel(
            plugin.d["config"][event.guild_id]["channel"]
        ).send(
            embed=await log_embed(
                content=event.content,
                guild_id=event.guild_id,
                user=event.author,
                channel=plugin.bot.cache.get_guild_channel(event.channel_id),
            )
        )


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and not event.content == None
        and not event.is_bot
    ):
        await check_blacklist(event)


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and not event.content == hikari.UNDEFINED
        and not event.is_bot
    ):
        await check_blacklist(event)


def load(bot):
    bot.add_plugin(plugin)
    main.load_plugin_configs("blacklist", plugin.d)


def unload(bot):
    bot.remove_plugin(plugin)
