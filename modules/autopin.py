from discord.ext import commands
import modules.db as db
from modules.util import config, module_enabled


class AutoPin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_roles(self, ctx):
        for role in ctx.message.author.roles:
            if role.name.lower() in {i.lower() for i in config[str(ctx.guild.id)]['autopin']['blacklisted_roles']}:
                return False
        return True

    async def check_channel(self, ctx):
        if config[str(ctx.guild.id)]['autopin']['whitelist']:
            return ctx.channel.id in config[str(ctx.guild.id)]['autopin']['list']
        else:
            return ctx.channel.id not in config[str(ctx.guild.id)]['autopin']['list']

    async def cog_check(self, ctx):
        return module_enabled('autopin', ctx.guild.id) and self.check_roles(ctx) and self.check_channel(ctx)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        server = config[str(user.guild.id)]
        tally = 0
        if user == self.bot.user:
            return
        db.try_create_table(f'pins_{user.guild.id}', ('message', 'users', 'tally'))

        if not reaction.emoji == server['autopin']['reaction'] or reaction.message.pinned:
            return

        if reaction.message.id not in db.query(f'select message from pins_{user.guild.id}'):
            db.insert(f'pins_{user.guild.id}', (reaction.message.id, user.id, 1))
            await reaction.message.add_reaction(reaction.emoji)
        else:
            if user.id not in db.query(f'select users from pins_{user.guild.id} where message = {reaction.message.id}'):
                tally = db.query(f'select tally from pins_{user.guild.id} where message = {reaction.message.id}')[0]
                db.c.execute(f'update pins_{user.guild.id} set tally = {tally + 1} '
                             f'where message = {reaction.message.id}')
                db.conn.commit()
        await reaction.message.remove_reaction(reaction.emoji, user)

        if tally == server['autopin']['threshold']:
            await reaction.message.pin()
            db.remove(f'pins_{user.guild.id}', f'message = {reaction.message.id}')


def setup(bot):
    bot.add_cog(AutoPin(bot))
