import discord.member
import modules.db as db
from discord.ext import commands
from modules.probate_meta import probate_user, unprobate_user
from modules.util import check_roles, config, list_prettyprint, module_enabled, parse_time, schedule_task, remove_task

class Probation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return check_roles('probate', ctx) and await module_enabled('probate', ctx.guild.id)


    @commands.command(aliases=['timeout'])
    async def probate(self, ctx, users: commands.Greedy[discord.Member], time: str = "24h", *, reason=""):
        """
        Locks users behind a probation role. This role will automatically be re-added if the user attempts to leave.
        Upon leaving, probation time will reset, and the user will be notified of such.
        """
        for user in users:
            await probate_user(user, time, reason)
        await ctx.send(f'{list_prettyprint(user.name for user in users)} banished to the Shadow Realm.')

    @commands.command(aliases=['untimeout'])
    async def unprobate(self, ctx, users: commands.Greedy[discord.Member]):
        """
        Immediately removes a user from probation, canceling the scheduled job.
        """
        for user in users:
            await unprobate_user(user)
        await ctx.send(f'{list_prettyprint(user.name for user in users)} released from the Shadow Realm.')

    @commands.command(aliases=['autotimeout'])
    async def autoprobate(self, ctx, state: bool = None):
        """
        Enables auto-probation. This will automatically add users to the database when they join.
        Only use in the event of raids.
        """
        config[str(ctx.guild.id)]['probate']['auto'] = state if state \
            else not config[str(ctx.guild.id)]['probate']['auto']
        await ctx.send(f'Auto-probation {"enabled" if config[str(ctx.guild.id)]["probate"]["auto"] else "disabled"}.')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server = config[str(member.guild.id)]
        if not await module_enabled('probate', member.guild.id): return
        if member.id in db.query(f'SELECT DISTINCT id FROM probations_{member.guild.id}'):
            await self.bot.get_channel(server['modlog_id']).send('Permission bypass detected, '
                                                                 f'probating {member.mention} and resetting timer.')
            time = db.query(f'SELECT DISTINCT time FROM probations_{member.guild.id} '
                                         f'WHERE id = {member.id}')[0]
            reason = db.query(f'SELECT DISTINCT reason FROM probations_{member.guild.id} where id = {member.id}')[0]
            await probate_user(member, time, reason)
            await member.send(f'You left {member.guild.name} while you were in probation, so the role has been '
                              'automatically re-applied. Additionally, your probation timer has reset.')

        if server['probate']['auto'] and member.id not in db.query(f'SELECT * from probations_{member.guild.id}'):
            db.insert(f'probations_{member.guild.id}', (int(member.id), 'Automatic probate.', '0s'))
            await member.add_roles(discord.utils.get(member.guild.roles,
                                                   name=config[str(member.guild.id)]['probate']['role_name']))
            await self.bot.get_channel(server['modlog_id']).send(f'Auto-probation enabled, probating {member.mention}.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not await module_enabled('probate', member.guild.id): return
        try:
            await remove_task(f'probation_{member.guild.id}_{member.id}')
        except Exception as e:
            print(Exception)
        channel = discord.utils.get(member.guild.channels, name=f"probation_{member.id}")
        if channel:
            await channel.delete()

def setup(bot):
    bot.add_cog(Probation(bot))
