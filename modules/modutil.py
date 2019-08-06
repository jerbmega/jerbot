from discord.ext import commands
from modules.util import config, write_message
import re


class ModUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #TODO add proper error handling to this def
    @commands.is_owner()
    @commands.command()
    async def announce(self, ctx, *, announcement):
        for server in config:
            if bool(re.search(r'\d', server)):
                try:
                    await write_message(config[server]['modlog_id'], f'**IMPORTANT:** {announcement}')
                except AttributeError:
                    await ctx.send(f'**CONFIGURATION ERROR**: {self.bot.get_guild(server).name} does not have a valid mod channel.' )


def setup(bot):
    bot.add_cog(ModUtil(bot))
