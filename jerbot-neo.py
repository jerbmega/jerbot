import logging.handlers
from sqlite3 import OperationalError

from discord.ext import commands
from discord import Forbidden
from modules.util import load_config, load_modules, bot, config

logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(filename='jerbot-neo.log', encoding='utf-8', mode='w', maxBytes=1000000,
                                               backupCount=1)
logger.addHandler(handler)


@bot.event
async def on_ready():
    print(f'Ready.\nLogged in as {bot.user.name}')


@bot.event
async def on_command_error(ctx, err):

    cmd = ctx.command
    err = getattr(err, 'original', err)

    if isinstance(err, commands.CommandNotFound):
        return
    elif isinstance(err, OperationalError):
        await ctx.send(f'{cmd} failed due to a database error: {err}')
    elif isinstance(err, commands.MissingPermissions) or isinstance(err, commands.CheckFailure):
        await ctx.send(f"You have insufficient permissions to run {cmd}.")
    elif isinstance(err, commands.BadArgument):
        await ctx.send(f"Bad argument was given to {cmd}.")
        await ctx.send_help(cmd)
    elif isinstance(err, commands.MissingRequiredArgument):
        await ctx.send(f"An argument required for {cmd} was missing.")
        await ctx.send_help(cmd)
    elif isinstance(err, Forbidden):
        await ctx.send(f"Bot is missing permissions necessary to run this command. {err}.")
    else:
        await ctx.send(f'An unexpected error occured when running {cmd}: {err}')

@bot.event
async def on_message(message):
    # jerbot-neo can dynamically change bot prefixes per-server, we are hijacking on_message to change it
    bot.command_prefix = config[str(message.guild.id)]['prefix']
    await bot.process_commands(message)

print('Initializing...')
print(f'Successfully loaded {" ".join(load_config())}' if load_config() else 'No config loaded.')
print(f'Successfully loaded {" ".join(load_modules())}')


bot.run(config['main']['token'])
