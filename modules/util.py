import os
import re
import yaml

from discord import Embed, channel, member
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


async def write_embed(channel: channel, member: member, color, title, event, avatar=True, footer=None, fields=None,
                      message=None):
    """
    :param channel: ID of the channel to send the log embed in.
    :param member: Member that is being referenced in this embed.
    :param color: Color of the embed.
    :param title: Title of the embed.
    :param event: Event that is triggering the embed write: Member Joined, Member Left, Member Banned, etc.
    :param avatar: If avatar should be displayed in moderation logs. Default: True
    :param fields: Optional. [[title, content]]
    :param footer: Optional. Footer for the embed.
    :param message: Optional. Message string to send alongside the embed.
    """
    if fields is None:
        fields = []
    embed = Embed(color=color, title=title)
    embed.set_author(name=event)
    if avatar:
        embed.set_thumbnail(url=member.avatar_url if member.avatar_url else member.default_avatar_url)
    if fields:
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=True)
    if footer:
        embed.set_footer(text=footer)
    await bot.get_channel(channel).send(message, embed=embed)


def check_perms(command):
    def predicate(ctx):
        for role in ctx.message.author.roles:
            if role.name.lower() in {i.lower() for i in config[str(ctx.message.guild.id)][command]['roles']}:
                return True
        return False
    return commands.check(predicate)