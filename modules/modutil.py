import discord.member
from discord.ext import commands
from modules.util import config, check_roles, write_message, list_prettyprint
import re


class ModUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(kick_members=True)
    @commands.command()
    async def kick(self, ctx, users: commands.Greedy[discord.Member], *, reason: str = None):
        """
        Kicks users from the server.
        """
        for user in users:
            await ctx.guild.kick(user, reason=f'{reason + " " if reason else ""}(Issued by {ctx.author.name})')
        await ctx.send(f'{list_prettyprint(user.name for user in users)} kicked.')

    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def ban(self, ctx, users: commands.Greedy[discord.User], *, reason: str = None):
        """
        Bans users from the server.
        """
        for user in users:
            await ctx.guild.ban(user, reason=f'{reason + " " if reason else ""}(Issued by {ctx.author.name})',
                                delete_message_days=0)
        await ctx.send(f'{list_prettyprint(user.name for user in users)} banned.')

    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def unban(self, ctx, users: commands.Greedy[discord.User], *, reason: str = None):
        """
        Unbans users from the server.
        """
        for user in users:
            await ctx.guild.unban(user, reason=f'{reason + " " if reason else ""}(Issued by {ctx.author.name})')
        await ctx.send(f'{list_prettyprint(user.name for user in users)} unbanned.')

    @check_roles('pins')
    @commands.command()
    async def pin(self, ctx, messages: commands.Greedy[discord.Message]):
        """
        Pins a message in a channel.
        """
        server = config[str(ctx.guild.id)]
        if ctx.channel.id not in server['pins']['channels'] and not \
                (role in ctx.author.roles for role in server['pins']['roles']):
            return
        for message in messages:
            await message.pin()
        await ctx.send(f"{list_prettyprint(str(message.id) for message in messages)} pinned.")

    @check_roles('pins')
    @commands.command()
    async def unpin(self, ctx, ids: commands.Greedy[discord.Message]):
        """
        Unpins a message in a channel.
        """
        server = config[str(ctx.guild.id)]
        if ctx.channel.id not in server['pins']['channels'] and not \
                (role in ctx.author.roles for role in server['pins']['roles']):
            return
        for id in ids:
            await message.unpin()
        await ctx.send(f"{list_prettyprint(str(message.id) for message in messages)} unpinned.")

    @check_roles('staff')
    @commands.command()
    async def purge(self, ctx, users: commands.Greedy[discord.Member], num: int):
        """
        Purges messages from the current channel.
        """

        def check(message):
            return message.author in users if users else True
        deletes = await ctx.channel.purge(limit=num + 1, check=check)

    @commands.is_owner()
    @commands.command()
    async def announce(self, ctx, *, announcement):
        """
        Announces a message to every server Jerbot is deployed in. Owner only.
        """
        for server in config:
            if bool(re.search(r'\d', server)):
                try:
                    await write_message(config[server]['modlog_id'], f'**IMPORTANT:** {announcement}')
                except AttributeError:
                    pass
                except discord.Forbidden:
                    await ctx.send(f"Skipped {server} due to permission issues.")
        await ctx.send("Announcement has been sent.")

    @commands.is_owner()
    @commands.command()
    async def global_ban(self, ctx, users: commands.Greedy[discord.User], *, reason: str = None):
        """
        Bans a user from every server Jerbot is deployed in. Dangerous. Owner only.
        Only use in the event that a user is a known raider or part of a spambot.
        """
        if not reason:
            reason = "No reason provided."

        edit_message = await ctx.send("Global in progress. This may take a long time.")
        for guild in self.bot.guilds:
            try:
                for user in users:
                    await guild.ban(user, reason=f"Global ban: {reason}")
            except discord.Forbidden:
                pass
        await edit_message.edit(content=f'{list_prettyprint(user.name for user in users)} globally banned.')


def setup(bot):
    bot.add_cog(ModUtil(bot))
