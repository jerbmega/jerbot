from discord.ext import commands
from os import listdir
from modules.util import list_prettyprint, load_config


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return commands.is_owner()

    def find_modules(self):
        modules = []
        for module in listdir('modules'):
            if module != "__pycache__":
                modules.append(module.split(".")[0])
        return modules

    @commands.command()
    async def insmod(self, ctx, *modules):
        """
        Adds a cog to the running instance of the bot. Owner only.
        """
        for module in modules:
            if module in self.find_modules():
                self.bot.load_extension('modules.' + module)
        await ctx.send(f'{list_prettyprint(modules)} unloaded.')

    @commands.command()
    async def rmmod(self, ctx, *modules):
        """
        Removes a cog from the running instance of the bot. Owner only.
        Certain cogs cannot be removed as they provide critical functionality.
        """
        required_modules = ["meta"]
        for module in modules:
            if module in self.find_modules() and module not in required_modules:
                self.bot.unload_extension('modules.' + module)
        await ctx.send(f'{list_prettyprint(modules)} unloaded.')

    @commands.command()
    async def reload(self, ctx, *modules):
        """
        Reloads a cog in the running instance of the bot. Owner only.
        """
        for module in modules:
            if module in self.find_modules():
                self.bot.unload_extension('modules.' + module)
                self.bot.load_extension('modules.' + module)
        await ctx.send(f'{list_prettyprint(modules)} reloaded.')

    @commands.command()
    async def reloadcfg(self, ctx):
        load_config()
        await ctx.send('Config reloaded.')

def setup(bot):
    bot.add_cog(Meta(bot))
