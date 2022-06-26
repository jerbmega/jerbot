import hikari
import lightbulb
from lightbulb.ext import tasks
import yaml

with open("config.yaml") as cfg:
    config = yaml.safe_load(cfg)


def load_config():
    bot.d = config


if __name__ == "__main__":
    bot = lightbulb.BotApp(token=config["token"])
    load_config()
    bot.load_extensions_from("plugins")
    tasks.load(bot)
    bot.run()


"""
TODO
Auto message functionality
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
