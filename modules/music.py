import youtube_dl
from discord.ext import commands
from modules.util import config, write_embed


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, play):
        server = config[str(ctx.guild.id)]
        if not server['voice']['enabled']:
            return
        await ctx.send("ok")
        await ctx.author.voice.channel.connect()
        await ctx.voice.play()

def setup(bot):
    bot.add_cog(Music(bot))
