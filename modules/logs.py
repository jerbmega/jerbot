from discord.ext import commands
from datetime import datetime
import modules.db as db


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        server_id = str(message.guild.id)
        db.try_create_table(f'logs_{server_id}', ('id', 'author', 'channel', 'content', 'time'))
        db.insert(f'logs_{server_id}', (message.id, message.author.id, message.channel.id, message.content,
                                        str(datetime.now())))


def setup(bot):
    bot.add_cog(Logs(bot))
