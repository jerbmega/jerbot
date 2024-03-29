import hikari
import miru
import lightbulb
import yaml
import os
import datetime
import traceback

import err
from scheduler import scheduler


def load_config():
    with open("config.yaml") as cfg:
        container = yaml.safe_load(cfg)
    return container


if __name__ == "__main__":
    intents = (
        hikari.Intents.ALL_UNPRIVILEGED
        | hikari.Intents.GUILD_MEMBERS
        | hikari.Intents.MESSAGE_CONTENT
    )
    config = load_config()
    bot = lightbulb.BotApp(
        token=config["token"],
        intents=intents,
    )

    @bot.listen(lightbulb.CommandErrorEvent)
    async def on_error(event: lightbulb.CommandErrorEvent) -> None:

        exception = event.exception.__cause__ or event.exception
        exceptions = [
            # General
            {
                "exception": lightbulb.NotOwner,
                "response": "Only the owner of the bot can do that.",
            },
            {
                "exception": lightbulb.MissingRequiredPermission,
                "response": "You have insufficient permissions to run this command.",
            },
            {
                "exception": lightbulb.CheckFailure,
                "response": "You have insufficient permissions to run this command.",
            },
            # Public roles
            {
                "exception": err.NoPublicRoles,
                "response": "You don't have any public roles!",
            },
            # AEGIS
            {
                "exception": err.NonAlphanumericGlobalBan,
                "response": "The provided URL must only have numeric ID's.",
            },
            {
                "exception": err.InvalidGlobalBanURL,
                "response": "The provided URL is incorrect or couldn't be reached.",
            },
            # Probations
            {
                "exception": err.UserNotInProbation,
                "response": "This user isn't in probation!",
            },
            {
                "exception": err.UnstrikeableRole,
                "response": "Users that can manage strikes can't be striked.",
            },
            {
                "exception": err.UserHasNoStrikes,
                "response": "This user has no strikes.",
            },
            {
                "exception": err.UnstrikeableBot,
                "response": "Bots can't be striked.",
            },
            # Watchlist
            {
                "exception": err.UserAlreadyWatched,
                "response": "This user is already in the watchlist.",
            },
        ]
        for response in exceptions:
            if isinstance(exception, response["exception"]):
                await event.context.respond(
                    response["response"], flags=hikari.MessageFlag.EPHEMERAL
                )
                return

        with open("/tmp/err.txt", "w+") as err_txt:
            err_txt.write(" ".join(traceback.format_exception(exception)))
        await event.context.respond(
            f"An unknown error occured trying to run `{event.context.command.name}`. Please see the attachment for more info.",
            flags=hikari.MessageFlag.EPHEMERAL,
            attachment="/tmp/err.txt",
        )
        os.remove(f"/tmp/err.txt")

    @bot.listen()
    async def start_scheduler(event: hikari.StartedEvent):
        scheduler.start()

    bot.d = load_config()
    bot.d["start_time"] = datetime.datetime.now()
    for folder in bot.d["plugin_folders"]:
        bot.load_extensions_from(folder)
    miru.install(bot)
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
