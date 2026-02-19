import fluxer
import yaml
import os

import err


def load_config():
    with open("config.yaml") as cfg:
        container = yaml.safe_load(cfg)
    return container


config = load_config()
bot = fluxer.Bot(command_prefix=config["prefix"], intents=fluxer.Intents.default())


# Annoyingly, these commands are bugged because of bugs in fluxer.py... how fun. They'll work when it's fixed.
@bot.command()
async def load(ctx, cog: str = None):
    try:
        if not ctx.author.id == config["owner"]:
            raise err.InsufficientPermissions

        cog_list = [
            f"{folder}.{cog.replace('.py', '')}"
            for folder in config["plugin_folders"]
            for cog in os.listdir(folder)
            if "pycache" not in cog
        ]
        if not cog:
            await ctx.reply(f"Available cogs: `{', '.join(cog_list)}`")
            return

        if cog not in cog_list:
            raise err.InvalidCog

        await bot.load_extension(cog)
        await ctx.reply(f"`{cog}` loaded.")

    except err.InsufficientPermissions:
        await ctx.reply("You have insufficient permissions to run this command.")
    except err.InvalidCog:
        await ctx.reply(
            f"This is not a valid cog.\nAvailable cogs: `{', '.join(cog_list)}`"
        )


@bot.command()
async def unload(ctx, cog: str = None):
    try:
        if not ctx.author.id == config["owner"]:
            raise err.InsufficientPermissions

        cog_list = [
            f"{folder}.{cog.replace('.py', '')}"
            for folder in config["plugin_folders"]
            for cog in os.listdir(folder)
            if "pycache" not in cog
        ]
        if not cog:
            await ctx.reply(f"Available cogs: `{', '.join(cog_list)}`")
            return

        if cog not in cog_list:
            raise err.InvalidCog

        await bot.unload_extension(cog)
        await ctx.reply(f"`{cog}` unloaded.")

    except err.InsufficientPermissions:
        await ctx.reply("You have insufficient permissions to run this command.")
    except err.InvalidCog:
        await ctx.reply(
            f"This is not a valid cog.\nAvailable cogs: `{', '.join(cog_list)}`"
        )


@bot.command()
async def reload(ctx, cog: str = None):
    try:
        if not ctx.author.id == config["owner"]:
            raise err.InsufficientPermissions

        cog_list = [
            f"{folder}.{cog.replace('.py', '')}"
            for folder in config["plugin_folders"]
            for cog in os.listdir(folder)
            if "pycache" not in cog
        ]
        if not cog:
            await ctx.reply(f"Available cogs: `{', '.join(cog_list)}`")
            return

        if cog not in cog_list:
            raise err.InvalidCog

        await bot.reload_extension(cog)
        await ctx.reply(f"`{cog}` reloaded.")

    except err.InsufficientPermissions:
        await ctx.reply("You have insufficient permissions to run this command.")
    except err.InvalidCog:
        await ctx.reply(
            f"This is not a valid cog.\nAvailable cogs: `{', '.join(cog_list)}`"
        )


@bot.event
async def on_ready():
    for folder in config["plugin_folders"]:
        for cog in os.listdir(folder):
            if "pycache" not in cog:
                await bot.load_extension(f"{folder}.{cog.replace('.py', '')}")

    print(f"Jerbot is ready to rumble!\nLogged in as {bot.user.username}")


if __name__ == "__main__":
    bot.run(config["token"])


def load_plugin_config(plugin: str):
    plugin_config = {}

    for config_file in os.listdir("server_configs"):
        if "sample.yaml" not in config_file:
            with open(f"server_configs/{config_file}") as cfg:
                server_id = int(config_file.split(".")[0])
                config = yaml.safe_load(cfg)

                if plugin in config:
                    plugin_config[server_id] = config[plugin]
    return plugin_config
