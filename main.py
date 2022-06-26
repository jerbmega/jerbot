import hikari
import lightbulb
import yaml

with open("config.yaml") as cfg:
    config = yaml.safe_load(cfg)

if __name__ == "__main__":
    bot = lightbulb.BotApp(token=config["token"])
    bot.load_extensions_from("plugins")
    bot.run()


"""
TODO
Auto message functionality
Blacklist functionality
Database parsing (use separate databases in a separate folder, use asqlite)
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
