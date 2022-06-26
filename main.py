import hikari
import lightbulb
import yaml
import os


def load_config():
    with open("config.yaml") as cfg:
        container = yaml.safe_load(cfg)
    return container


if __name__ == "__main__":
    config = load_config()
    bot = lightbulb.BotApp(token=config["token"])
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
                if not server_id in datastore["config"]:
                    datastore["config"][server_id] = {}
                datastore["config"][server_id] = yaml.safe_load(cfg)["automessage"]


"""
TODO
Blacklist functionality
Eagle Eye
Item functionality
Levenshtein distance filtering (thefuzz + score?)
Modlogs
Moderation utilities (most of these are probably retired in favor of slash commands)
Platinum God parsing
Probation functionality
Role join/leave system
Strikes
Wiki parsing
"""
