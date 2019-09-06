import discord.member
import modules.db as db
from discord.ext import commands
from apscheduler.jobstores.base import JobLookupError
from modules.util import check_roles, config, list_prettyprint, module_enabled, parse_time, schedule_task, remove_task


class Probation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return check_roles('probate', ctx) and await module_enabled('probate', ctx.guild.id)

    async def remove_probate(self, ctx, user, id):
        db.remove(f'probations_{id}', f'id = {user.id}')
        await user.remove_roles(discord.utils.get(ctx.guild.roles,
                                                  name=config[str(ctx.guild.id)]['probate']['role_name']))

    @commands.command()
    async def probate(self, ctx, users: commands.Greedy[discord.Member], time: str = "24h", *, reason=""):
        """
        Locks users behind a probation role. This role will automatically be re-added if the user attempts to leave.
        Upon leaving, probation time will reset, and the user will be notified of such.
        """
        timedelta = await parse_time(time)
        db.try_create_table(f'probations_{ctx.guild.id}', ('id', 'reason', 'time'))
        for user in users:
            await schedule_task(self.remove_probate, timedelta, f'probation_{ctx.guild.id}_{user.id}',
                                [ctx, user, ctx.guild.id])
            db.insert(f'probations_{ctx.guild.id}', (user.id, reason, time))
            await user.add_roles(discord.utils.get(ctx.guild.roles,
                                                   name=config[str(ctx.guild.id)]['probate']['role_name']))


        print(db.query(f'SELECT reason FROM probations_{ctx.guild.id}'))
        await ctx.send(f'{list_prettyprint(user.name for user in users)} banished to the Shadow Realm.')

    @commands.command()
    async def unprobate(self, ctx, users: commands.Greedy[discord.Member]):
        """
        Immediately removes a user from probation, canceling the scheduled job.
        """
        for user in users:
            try:
                await remove_task(f'probation_{ctx.guild.id}_{user.id}')
            except JobLookupError:
                pass #TODO proper error handling
            await user.remove_roles(discord.utils.get(ctx.guild.roles,
                                                      name=config[str(ctx.guild.id)]['probate']['role_name']))
            db.remove(f'probations_{ctx.guild.id}', f'id = {user.id}')
        await ctx.send(f'{list_prettyprint(user.name for user in users)} released from the Shadow Realm.')

    @commands.command()
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
        if not module_enabled('probate', member.guild.id): return
        query = db.query(f'SELECT * from probations_{member.guild.id}')
        if member.id in db.query(f'SELECT DISTINCT id FROM probations_{member.guild.id}'):
            await self.bot.get_channel(server['modlog_id']).send('Permission bypass detected, '
                                                                 f'probating {member.mention} and resetting timer.')

            time = await parse_time(db.query(f'SELECT DISTINCT time FROM probations_{member.guild.id} '
                                         f'WHERE id = {member.id}')[0])
            print(time)
            await schedule_task(self.remove_probate, time,
                                f'probation_{member.guild.id}_{member.id}', [member, member, member.guild.id])
            await member.add_roles(discord.utils.get(member.guild.roles,
                                                   name=server['probate']['role_name']))
            await member.send(f'You left {member.guild.name} while you were in probation, so the role has been '
                              'automatically re-applied. Additionally, your probation timer has reset.')

        if server['probate']['auto'] and member.id not in db.query(f'SELECT * from probations_{member.guild.id}'):
            db.insert(f'probations_{member.guild.id}', (int(member.id), 'Automatic probate.', '0s'))
            await member.add_roles(discord.utils.get(member.guild.roles,
                                                   name=config[str(member.guild.id)]['probate']['role_name']))
            await self.bot.get_channel(server['modlog_id']).send('Auto-probation enabled, probating {member.mention}.')

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        if module_enabled('probate', member.guild.id) and member.id in db.query(
                f'SELECT DISTINCT id FROM probations_{member.guild.id}'):
            try:
                await remove_task(f'probation_{member.guild.id}_{member.id}')
            except JobLookupError:
                pass #TODO proper error handling

def setup(bot):
    bot.add_cog(Probation(bot))
