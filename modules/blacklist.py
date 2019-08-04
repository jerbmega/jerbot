import re

from discord.ext import commands
from modules.util import config, write_embed


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_blacklist(self, message):
        server = config[str(message.guild.id)]
        if not server['blacklist']['enabled'] or message.author == self.bot.user:
            return
        for role in message.author.roles:
            if role.name.lower() in {i.lower() for i in server['blacklist']['overrides']}:
                raise Exception("User is whitelisted.")
        for deletion in server['blacklist']['deletions']:
            for trigger in deletion['trigger']:
                if trigger in re.sub(r'\s+', '', message.content.lower()):
                    await message.delete()
                    await message.author.send(deletion['response'] + server['footer'])
                    await write_embed(server['modlog_id'], message.author, server['blacklist']['embed_color'],
                                      f'Message matched deletion pattern {deletion["trigger"]}', 'Blacklisted phrase.',
                                      fields=[['Message content', message.content]],
                                      message=f'{message.author.mention} {deletion["log"]} in {message.channel.id}')

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.check_blacklist(message)

    @commands.Cog.listener()
    async def on_message_edit(self, old_message, message):
        await self.check_blacklist(message)


def setup(bot):
    bot.add_cog(Blacklist(bot))
