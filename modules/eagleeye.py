from discord.ext import commands
import modules.db as db
import discord.member
import typing
from modules.util import config, check_roles, list_prettyprint, module_enabled, write_embed


class EagleEye(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return check_roles('eagleeye', ctx) and await module_enabled('eagleeye', ctx.guild.id)

    @commands.command()
    async def watch(self, ctx, users: commands.Greedy[discord.Member], *, reason: typing.Optional[str] = ''):
        """
        Adds problematic users to the watchlist.
        """
        db.try_create_table(f'eagleeye_{ctx.guild.id}', ('id', 'username', 'reason'))
        for user in users:
            db.insert(f'eagleeye_{ctx.guild.id}', (int(user.id), self.bot.get_user(int(user.id)).name, reason))
        await ctx.send(f'{list_prettyprint(user.name for user in users)} added to the watchlist.')

    @commands.command()
    async def unwatch(self, ctx, users: commands.Greedy[discord.Member]):
        """
        Removes users from the watchlist.
        """
        for user in users:
            db.remove(f'eagleeye_{ctx.guild.id}', f'id = {user.id}')
        await ctx.send(f'{list_prettyprint(user.name for user in users)} removed from the watchlist.')

    @commands.command()
    async def watchlist(self, ctx, user: typing.Optional[discord.Member]):
        """
        Prints a list of users in the watchlist.
        Providing no arguments will return a list of watched ID's.
        Provide a watched ID or user mention for reasoning, if a reason was provided.
        """
        if not user:
            await ctx.send('I have eyes on '
                           f'{list_prettyprint(db.query(f"SELECT DISTINCT username FROM eagleeye_{ctx.guild.id}"))}')
        else:
            await ctx.send(f'{user.name} was watched for reason ' +
                           list_prettyprint(db.query(f"SELECT DISTINCT reason from eagleeye_{ctx.guild.id} "
                                                     f"where id = {user.id}")))

    @commands.command()
    async def watch_purge(self, ctx):
        """
        Removes users that are no longer in the server from the watchlist.
        """
        for id in db.query(f"SELECT DISTINCT username FROM eagleeye_{ctx.guild.id}"):
            if not self.bot.get_user(id):
                db.remove(f'eagleeye_{ctx.guild.id}', f'id = {id}')
        await ctx.send('Purged.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await module_enabled('eagleeye', message.guild.id): return
        if message.author.id in db.query(f'SELECT DISTINCT id from eagleeye_{message.guild.id}'):
            server = config[str(message.guild.id)]
            fields = [['Message content', message.content]]
            for attachment in message.attachments:
                fields.append(['Attachment', attachment.proxy_url])

            await write_embed(server['modlog_id'], message.author, server['eagleeye']['embed_color'],
                              f'{message.author.name} ({message.author.id})',
                              description=f'[#{message.channel.name}]'
                                          f'(https://discordapp.com/channels/{message.guild.id}/{message.channel.id}'
                                          f'/{message.id})',
                              fields=fields)

    @commands.Cog.listener()
    async def on_message_edit(self, old_message, message):
        if not await module_enabled('eagleeye', message.guild.id) or old_message.content == message.content: return
        if message.author.id in db.query(f'SELECT DISTINCT id from eagleeye_{message.guild.id}'):
            server = config[str(message.guild.id)]
            fields = [['Old message', old_message.content], ['New message', message.content]]
            for attachment in message.attachments:
                fields.append(['Attachment', attachment.proxy_url])

            await write_embed(server['modlog_id'], message.author, server['eagleeye']['embed_color'],
                              f'{message.author.name} ({message.author.id}) **edited a message.**',
                              description=f'[#{message.channel.name}](https://discordapp.com/channels/'
                                          f'{message.guild.id}/{message.channel.id}/{message.id})',
                              fields=fields)


def setup(bot):
    bot.add_cog(EagleEye(bot))
