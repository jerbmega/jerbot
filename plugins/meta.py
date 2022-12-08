# This plugin handles insertion, deletion, and reloading of plugins.

import hikari
import lightbulb

import os
import main

plugin = lightbulb.Plugin("Meta")
plugin.add_checks(lightbulb.owner_only)


def find_plugins(safe: bool = False):
    plugins = []
    blacklist = ["__pycache__"]
    if safe:  # Prevent critical modules (like this one!) from being unloaded
        blacklist.append("meta.py")
    for folder in main.load_config()[
        "plugin_folders"
    ]:  # This runs too early to properly get this from the datastore
        for plugin in os.listdir(folder):
            if plugin not in blacklist:
                plugins.append(f"{folder}.{plugin.split('.')[0]}")
    return plugins


@plugin.command
@lightbulb.option("plugin", "Plugin to reload", choices=find_plugins())
@lightbulb.command("reload", "Reload a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def reload(ctx: lightbulb.Context) -> None:
    ctx.bot.reload_extensions(ctx.options.plugin)
    await ctx.respond(
        f"Reloaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.command
@lightbulb.option("plugin", "Plugin to unload", choices=find_plugins(True))
@lightbulb.command("unload", "Unload a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def unload(ctx: lightbulb.Context) -> None:
    ctx.bot.unload_extensions(ctx.options.plugin)
    await ctx.respond(
        f"Unloaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.command
@lightbulb.option("plugin", "Plugin to load", choices=find_plugins())
@lightbulb.command("load", "Load a plugin")
@lightbulb.implements(lightbulb.SlashCommand)
async def load(ctx: lightbulb.Context) -> None:
    ctx.bot.load_extensions(ctx.options.plugin)
    await ctx.respond(
        f"Loaded {ctx.options.plugin}.", flags=hikari.MessageFlag.EPHEMERAL
    )


@plugin.command
@lightbulb.command("resync_commands", "Resyncs slash commands with Discord")
@lightbulb.implements(lightbulb.SlashCommand)
async def resync_commands(ctx: lightbulb.Context) -> None:
    await ctx.bot.sync_application_commands()
    await ctx.respond("Done.")


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
