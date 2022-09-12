# This plugin logs messages into a database.

import hikari
import lightbulb
import asyncio
from datetime import datetime

import db
import main

plugin = lightbulb.Plugin("Logs", include_datastore=True)


async def log_message(event: hikari.Event):
    if (
        event.guild_id in plugin.d["config"]
        and not event.message.content == hikari.UNDEFINED
    ):
        await db.insert(
            "logs",
            f"guild_{event.guild_id}",
            (
                event.message_id,
                event.author_id,
                event.channel_id,
                event.message.content,
                datetime.now().timestamp(),
            ),
        )


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    await log_message(event)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent) -> None:
    await log_message(event)


def load(bot):
    bot.add_plugin(plugin)
    main.load_plugin_configs("logs", plugin.d)
    for guild in plugin.d["config"]:
        asyncio.run(
            db.create_table(
                "logs", f"guild_{guild}", ("id", "author", "channel", "content", "time")
            )
        )


def unload(bot):
    bot.remove_plugin(plugin)
