import fluxer
import yaml
import os


def load_config():
    with open("config.yaml") as cfg:
        container = yaml.safe_load(cfg)
    return container


config = load_config()
bot = fluxer.Bot(command_prefix=config["prefix"], intents=fluxer.Intents.default())


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
