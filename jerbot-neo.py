import logging.handlers
import os
import re
import yaml

from discord.ext import commands
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
async def on_message(message):
    # jerbot-neo can dynamically change bot prefixes per-server, we are hijacking on_message to change it
    bot.command_prefix = config[str(message.guild.id)]['prefix']
    await bot.process_commands(message)

# TODO *global* error handling, none of this try/except trash every two lines
# TODO add docstrings
# TODO proper permission management this time

print('Initializing...')
print(f'Successfully loaded {" ".join(load_config())}' if load_config() else 'No config loaded.')
print(f'Successfully loaded {" ".join(load_modules())}')

bot.run(config['main']['token'])