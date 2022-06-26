# This plugin handles insertion, deletion, and reloading of plugins.

import hikari
import lightbulb

import db
import os
from main import config

plugin = lightbulb.Plugin("Meta")
plugin.add_checks(lightbulb.owner_only)


def find_plugins(safe: bool = False):
    plugins = []
    blacklist = ["__pycache__"]
    if safe:  # Prevent critical modules (like this one!) from being unloaded
        blacklist.append("meta.py")
    for plugin in os.listdir("plugins"):
        if plugin not in blacklist:
            plugins.append(plugin.split(".")[0])
    return plugins


@plugin.command
@lightbulb.option("plugin", "Plugin to reload", choices=find_plugins())
@lightbulb.command("reload", "Reload a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def reload(ctx: lightbulb.Context) -> None:
    ctx.bot.reload_extensions(f"plugins.{ctx.options.plugin}")
    await ctx.respond(
        f"Reloaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.command
@lightbulb.option("plugin", "Plugin to unload", choices=find_plugins(True))
@lightbulb.command("unload", "Unload a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def unload(ctx: lightbulb.Context) -> None:
    ctx.bot.unload_extensions(f"plugins.{ctx.options.plugin}")
    await ctx.respond(
        f"Unloaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.command
@lightbulb.option("plugin", "Plugin to load", choices=find_plugins())
@lightbulb.command("load", "Load a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def load(ctx: lightbulb.Context) -> None:
    ctx.bot.load_extensions(f"plugins.{ctx.options.plugin}")
    await ctx.respond(
        f"Loaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.set_error_handler()
async def command_error_handler(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    response = f"An unknown error occured trying to perform this action: {exception}"
    await event.context.respond(response, flags=hikari.MessageFlag.EPHEMERAL)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
