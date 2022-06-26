# This plugin handles automatic sending of messages in channels on a specific time.

import asyncio
import hikari
import lightbulb
from lightbulb.ext import tasks
from apscheduler.triggers.cron import CronTrigger

import main
from scheduler import scheduler

plugin = lightbulb.Plugin("Auto Message", include_datastore=True)


async def send_message(channel_id: int, content: str):
    await plugin.bot.cache.get_guild_channel(channel_id).send(content)


def load(bot):
    bot.add_plugin(plugin)
    main.load_plugin_configs("automessage", plugin.d)
    plugin.d["tasks"] = []
    for server in plugin.d["config"]:
        for task in plugin.d["config"][server]:
            task = scheduler.add_job(
                send_message,
                CronTrigger.from_crontab(task["crontab"]),
                id=f"automessage_{server}_{task['channel']}_{task['message']}_{task['crontab']}",
                replace_existing=True,
                args=(
                    task["channel"],
                    task["message"],
                ),
            )
            plugin.d["tasks"].append(task)


def unload(bot):
    for task in plugin.d["tasks"]:
        task.remove()
    bot.remove_plugin(plugin)
