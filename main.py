import hikari
import lightbulb
import yaml
import os


def load_config():
    with open("config.yaml") as cfg:
        container = yaml.safe_load(cfg)
    return container


if __name__ == "__main__":
    intents = hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.GUILD_MEMBERS
    config = load_config()

    bot = lightbulb.BotApp(
        token=config["token"],
        default_enabled_guilds=(config["testing_guild"]),
        intents=intents,
    )  # TODO remove enabled guilds for production
    bot.d = load_config()
    bot.load_extensions_from("plugins")
    bot.run()


def load_plugin_configs(plugin: str, datastore: lightbulb.utils.data_store.DataStore()):
    for config in os.listdir("server_configs"):
        if not "config" in datastore:
            datastore["config"] = {}

        if "sample.yaml" not in config:
            with open(f"server_configs/{config}") as cfg:
                server_id = int(config.split(".")[0])
                config = yaml.safe_load(cfg)

                if plugin in config:
                    datastore["config"][server_id] = config[plugin]


"""
TODO
Item functionality
Moderation utilities (most of these are probably retired in favor of slash commands)
Probation functionality
Role join/leave system
Strikes
"""

"""
TODO Book of Secrets submodule
Item functionality
Platinum God parsing
Wiki parsing
"""
