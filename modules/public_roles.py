from discord.ext import commands
import discord.member
from modules.util import config, list_prettyprint, module_enabled


class PublicRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return module_enabled('public_roles', ctx.guild.id)

    @commands.command()
    async def join(self, ctx, roles: commands.Greedy[discord.Role]):
        """
        Joins a role specified as a public role for this server.
        You can list public roles using the listroles command.
        """
        server = config[str(ctx.guild.id)]
        successful = []
        for role in roles:
            if role.name in server['public_roles']['public_roles']:
                await ctx.author.add_roles(role)
                successful.append(role.name)
        await ctx.send(f'Successfully joined {list_prettyprint(successful)}')

    @commands.command()
    async def leave(self, ctx, roles: commands.Greedy[discord.Role]):
        """
        Leaves a role specified as a public role for this server.
        You can list public roles using the listroles command.
        """
        server = config[str(ctx.guild.id)]
        successful = []
        for role in roles:
            if role.name in server['public_roles']['public_roles']:
                await ctx.author.remove_roles(role)
                successful.append(role.name)
        await ctx.send(f'Successfully joined {list_prettyprint(successful)}')

    @commands.command()
    async def listroles(self, ctx):
        """
        Lists public roles for this server.
        """
        server = config[str(ctx.guild.id)]
        await ctx.send(list_prettyprint(server['public_roles']['public_roles']))


def setup(bot):
    bot.add_cog(PublicRoles(bot))
