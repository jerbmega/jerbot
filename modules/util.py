import yaml, os, re
from discord.ext import commands

bot = commands.Bot(command_prefix="!")
config = {}
# TODO aliases were never fully implemented in jerbot2, figure this out

def list_prettyprint(old_list: list):
    """
    Prepares a list for easier viewing on Discord.
    Example:
        list_prettyprint([foo, bar])
    Returns:
        `foo, bar`
    """
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
            print(f'Failed to load {extension}. ({e})')
    return successful
