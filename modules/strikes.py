import datetime
import re
import discord.member
import modules.db as db
from modules.probate_meta import probate_user, unprobate_user
from discord.ext import commands
from apscheduler.jobstores.base import JobLookupError
from sqlite3 import OperationalError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from modules.util import check_roles, config, list_prettyprint, module_enabled, remove_task, write_embed, parse_time, \
    scheduler


async def remove_strike(server, strike):
    db.remove(f'strikes_{server}', f'id = {strike[0]} and time = {strike[3]}')
    await write_embed(config[str(server)]['modlog_id'], member=None, color=config[str(server)]['strikes']['embed_color'],
                      title=strike[2], avatar=False,
                      message=f'**Strike removed:** A temporary strike for <@{strike[0]}> has expired.')

class Strikes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return check_roles('strikes', ctx) and await module_enabled('strikes', ctx.guild.id)

    @commands.command()
    async def strike(self, ctx, users: commands.Greedy[discord.Member], time: str, *, reason: str=None):
        """
        Strikes a user, leaving a mark on the record. A 24 hour probation is automatically applied.
        Strikes will be removed from the record after a set time period, if provided.
        Examples:
            .strike @jerb#6464 1w spam
        """
        server = config[str(ctx.guild.id)]

        if await parse_time(time):
            delta = await parse_time(time)
            time = datetime.datetime.now() + delta
            time = time.timestamp()
        if isinstance(time, str):
            reason = f'{time} {reason}'.rstrip() if reason else time

        db.try_create_table(f'strikes_{ctx.guild.id}', ('id', 'issuer', 'reason', 'time'))
        for user in users:
            try:
                await remove_task(f'probation_{ctx.guild.id}_{user.id}')
            except JobLookupError:
                pass #TODO proper error handling
            await probate_user(user, "24h", reason)
            db.insert(f'strikes_{ctx.guild.id}', (user.id, ctx.author.id, reason,
                                                  time if not isinstance(time, str) else "None"))
            amount = len(db.query(f'SELECT reason from strikes_{ctx.guild.id} WHERE id = {user.id}'))
            await write_embed(server['modlog_id'], member=None, color=server['strikes']['embed_color'], title=reason,
                              event=ctx.author.name, avatar=False,
                              message=f'**Strike issued:** {user.mention} has received strike {amount}. ' +
                                      (f'This strike will expire on '
                              f'{datetime.datetime.utcfromtimestamp(time).replace(microsecond=0)} UTC.'
                              if not isinstance(time, str) else ""))
            base_message = f'You have been **striked** on {ctx.guild.name}. This is strike {amount}.\n' + \
                           f'The provided reason is `{reason}`. '
            if not isinstance(time, str):
                base_message = base_message + f"\nThis strike is **temporary**, and is set to expire on " \
                                              f"{datetime.datetime.utcfromtimestamp(time).replace(microsecond=0)} UTC. You will be removed from probation in 24 hours."

                scheduler.add_job(remove_strike, 'date', run_date=datetime.datetime.fromtimestamp(time),
                                  args=[ctx.guild.id, [user.id, ctx.author.id, reason, time]], id=f"strikeremoval_{server}_{time}")
            if server['strikes']['ban']['enabled'] and amount >= server['strikes']['ban']['amount']:
                await user.send(base_message + f'As this is strike {amount}, you have been automatically banned.')
                try:
                    await remove_task(f'probation_{ctx.guild.id}_{user.id}')
                except JobLookupError:
                    pass  # TODO proper error handling
                await ctx.guild.ban(user)
            elif server['strikes']['kick']['enabled'] and amount >= server['strikes']['kick']['amount']:
                await user.send(base_message + f'As this is strike {amount}, you have been automatically kicked.')
                try:
                    await remove_task(f'probation_{ctx.guild.id}_{user.id}')
                except JobLookupError:
                    pass  # TODO proper error handling
                await ctx.guild.kick(user)
            else:
                await user.send(base_message)
        await ctx.send(f'{list_prettyprint(user.name for user in users)} striked.')

    @commands.command()
    async def delstrike(self, ctx, user: discord.Member, index: int):
        """
        Deletes a strike for a user.
        Automatically removes probation, if any.
        """
        server = config[str(ctx.guild.id)]
        strikes = db.query(f'SELECT reason from strikes_{ctx.guild.id} WHERE id = {user.id}')
        try:
            await remove_task(f'probation_{ctx.guild.id}_{user.id}')
        except JobLookupError:
            pass #TODO proper error handling
        try:
            await unprobate_user(user)
        except Exception as e:
            pass
        removal = strikes[index - 1]
        db.remove(f'strikes_{ctx.guild.id}', f'id = {user.id} and reason = "{removal}"')
        await user.send(f'You have been pardoned of a strike on {ctx.guild.name}. ' \
                       f'You now have {len(strikes) - 1} strikes. The removed strike was `{removal}`.')


    @commands.command()
    async def liststrikes(self, ctx, user):
        """
        List strikes for a user. Provides strike numbers, which are necessary for the delstrike command.
        """
        server = config[str(ctx.guild.id)]
        user = re.sub(r"\D", "", user)
        strikes = db.query(f'SELECT reason from strikes_{ctx.guild.id} WHERE id = {user}')
        fields = []
        try:
            name = self.bot.get_user(int(user)).name
        except:
            name = None
        for i, strike in enumerate(strikes, 1):
            fields.append([f"Strike {i}", strike])

        await write_embed(ctx.channel.id, None, server['strikes']['embed_color'],
                          f"Strikes for {'unknown ' if not name else ''}user {name if name else user}",
                          avatar=False, footer="None!" if not strikes else None, fields=fields if fields else None)


def setup(bot):
    for server in config:
        if bool(re.search(r'\d', server)) and config[server]['strikes']['enabled']:
            try:
                db.c.row_factory = lambda cursor, row: row
                strikes = db.query(f"select * from strikes_{server}")
                db.c.row_factory = lambda cursor, row: row[0]
                for i, strike in enumerate(strikes):
                    if strike[3]:
                        scheduler.add_job(remove_strike, 'date', run_date=datetime.datetime.fromtimestamp(strike[3]),
                                          args=[server, strike], id=f"strikeremoval_{server}_{i}")
            except OperationalError:
                pass
            except TypeError:
                pass
    bot.add_cog(Strikes(bot))
