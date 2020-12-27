import discord
import modules.db as db
from apscheduler.jobstores.base import JobLookupError
from modules.util import config, schedule_task, remove_task, parse_time


async def probate_user(user, time, reason):
    timedelta = await parse_time(time)
    db.try_create_table(f'probations_{user.guild.id}', ('id', 'reason', 'time'))
    category = discord.utils.get(user.guild.categories, name="Probations")
    role = discord.utils.get(user.guild.roles, name=config[str(user.guild.id)]['probate']['role_name'])
    channel = discord.utils.get(user.guild.channels, name=f'probation_{user.id}')
    overwrites = {
        user.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user.guild.me: discord.PermissionOverwrite(read_messages=True),
    }
    for staff_role in config[str(user.guild.id)]['probate']['roles']:
        staff_role = discord.utils.get(user.guild.roles, name=staff_role)
        overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True)

    if not category:
        category_overwrites = overwrites
        category_overwrites[role] = discord.PermissionOverwrite(read_messages=False)
        category = await user.guild.create_category("Probations", overwrites=category_overwrites)
    overwrites[user] = discord.PermissionOverwrite(read_messages=True)
    if not channel:
        channel = await user.guild.create_text_channel(f'probation_{user.id}', overwrites=overwrites,
                                                       category=category,
                                                       topic=f'{user.mention} - {time} - {reason}')
    else:
        await channel.set_permissions(user, overwrite=discord.PermissionOverwrite(read_messages=True))
    try:
        await schedule_task(unprobate_user, timedelta, f'probation_{user.guild.id}_{user.id}',
                        [user])
    except:
        pass
    db.insert(f'probations_{user.guild.id}', (user.id, reason, time))
    await user.add_roles(role)


async def unprobate_user(user):
    try:
        await remove_task(f'probation_{user.guild.id}_{user.id}')
    except JobLookupError:
        pass  # TODO proper error handling
    await user.remove_roles(discord.utils.get(user.guild.roles,
                                              name=config[str(user.guild.id)]['probate']['role_name']))
    channel = discord.utils.get(user.guild.text_channels, name=f"probation_{user.id}")
    await channel.delete()
    db.remove(f'probations_{user.guild.id}', f'id = {user.id}')
