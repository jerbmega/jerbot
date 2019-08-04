import logging.handlers
import os
import re
import yaml

from discord.ext import commands

# Initialize configuration
config = {}
# TODO aliases were never fully implemented in jerbot2, figure this out


def list_prettyprint(old_list: list):
    '''
    Prepares a list for easier viewing on Discord.
    Example:
        list_prettyprint([foo, bar])
    Returns:
        `foo, bar`
    '''
    return f'`{", ".join(old_list)}`'


def load_config():
    successful = []
    with open('config.yaml') as cfg:
        try:
            config['main'] = yaml.safe_load(cfg)
            successful.append('main')
        except Exception as e:
            print(f'Failed to load main configuration. ({e})')

    for name in os.listdir('config'):
        if name.startswith('config') and name.endswith('yaml'):
            server_id = re.sub(r'\D', '', name)
            with open('config/' + name) as cfg:
                try:
                    config[server_id] = yaml.safe_load(cfg)
                    successful.append(server_id)
                except Exception as e:
                    print('Failed to load {name}. ({e})')
    return successful


def load_modules():
    successful = []
    for extension in sorted(config['main']['extensions']):
        try:
            bot.load_extension(f'modules.{extension}')
            successful.append(extension)
        except Exception as e:
            print(f'Failed to load {extension}. ({e}')
    return successful


logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(filename='jerbot-neo.log', encoding='utf-8', mode='w', maxBytes=1000000,
                                               backupCount=1)
logger.addHandler(handler)

bot = commands.Bot(command_prefix="!")
bot.config = config

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
print(f'Successfully loaded {" ".join(load_modules())}' if load_modules() else 'No modules loaded.')

bot.run(config['main']['token'])