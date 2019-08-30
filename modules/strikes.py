import re
import discord.member
import modules.db as db
from discord.ext import commands
from apscheduler.jobstores.base import JobLookupError
from modules.util import check_roles, config, list_prettyprint, module_enabled, parse_time, schedule_task, remove_task, \
    write_embed


class Strikes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await check_roles('strikes', ctx) and await module_enabled('strikes', ctx.guild.id)

    async def remove_probate(self, ctx, user, id):
        db.remove(f'probations_{id}', f'id = {user.id}')
        await user.remove_roles(discord.utils.get(ctx.guild.roles,
                                                  name=config[str(ctx.guild.id)]['probate']['role_name']))

    @commands.command()
    async def strike(self, ctx, users: commands.Greedy[discord.Member], *, reason):
        """
        Strikes a user, leaving a permanent mark on the record.
        A 24 hour probation will additionally be applied.
        """
        server = config[str(ctx.guild.id)]
        timedelta = await parse_time('24h')
        db.try_create_table(f'strikes_{ctx.guild.id}', ('id', 'issuer', 'reason'))
        db.try_create_table(f'probations_{ctx.guild.id}', ('id', 'reason', 'time'))
        for user in users:
            await schedule_task(self.remove_probate, timedelta, f'probation_{ctx.guild.id}_{user.id}',
                                [ctx, user, ctx.guild.id])
            db.insert(f'probations_{ctx.guild.id}', (user.id, reason, '24h'))
            await user.add_roles(discord.utils.get(ctx.guild.roles,
                                                   name=config[str(ctx.guild.id)]['probate']['role_name']))
            db.insert(f'strikes_{ctx.guild.id}', (user.id, ctx.author.id, reason))
            amount = len(db.query(f'SELECT reason from strikes_{ctx.guild.id} WHERE id = {user.id}'))
            await write_embed(server['modlog_id'], member=None, color=server['strikes']['embed_color'], title=reason,
                              event=ctx.author.name, avatar=False,
                              message=f'**Strike issued:** {user.mention} has received strike {amount}.')
            base_message = f'You have been **striked** on {ctx.guild.name}. This is strike {amount}.\n' + \
                           f'The provided reason is `{reason}`. '
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
        db.remove(f'probations_{ctx.guild.id}', f'id = {user.id}')
        await user.remove_roles(discord.utils.get(ctx.guild.roles,
                                                    name=config[str(ctx.guild.id)]['probate']['role_name']))

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
    bot.add_cog(Strikes(bot))
