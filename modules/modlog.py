from discord import ClientUser
from discord.ext import commands
from modules.util import config, write_embed


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server = config[str(member.guild.id)]
        if server['greeting']['enabled']:
            await member.send(f"Welcome to the {member.guild.name} server, {member.mention}!"
                              f" {server['greeting']['message'] + server['footer']}")
        if not server['join_leave_logs']['enabled']:
            return
        account_age = member.joined_at - member.created_at
        color = server['join_leave_logs']['warn_color'] if account_age.days < 7 \
            else server['join_leave_logs']['join_color']
        fields = [['Account Creation Date', f'{str(member.created_at)[:-7]} UTC'], ['User ID', member.id],
                  ['Account Age', account_age]]
        await write_embed(server['modlog_id'], member, color, f'{member.name}#{member.discriminator}', 'Member joined.',
                          fields=fields)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        server = config[str(member.guild.id)]
        if not server['join_leave_logs']['enabled']:
            return
        fields = [['User ID', member.id], ['Nickname', member.nick]]
        await write_embed(server['modlog_id'], member, server['join_leave_logs']['leave_color'],
                          f'{member.name}#{member.discriminator}', 'Member left.', fields=fields)

    @commands.Cog.listener()
    async def on_member_ban(self, member):
        server = config[str(member.guild.id)]
        if not server['join_leave_logs']['enabled']:
            return
        await write_embed(server['modlog_id'], member, server['join_leave_logs']['leave_color'],
                          f'{member.name}#{member.discriminator}', 'Member banned.')

    @commands.Cog.listener()
    async def on_message_edit(self, message, new_message):
        server = config[str(message.guild.id)]
        if not server['join_leave_logs']['enabled'] or not server['join_leave_logs']['extended'] \
                or message.author == ClientUser or message.content == new_message.content:
            return
        fields = [['Channel', f'<#{message.channel.id}>'], ['Before', message.content], ['After', new_message.content]]
        for attachment in new_message.attachments:
            fields.append(["Attachment URL", attachment.proxy_url])
        await write_embed(server['modlog_id'], message.author, server['join_leave_logs']['leave_color'],
                          f'{message.author.name}#{message.author.discriminator}', 'Message edited.', fields=fields)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        server = config[str(message.guild.id)]
        if not server['join_leave_logs']['enabled'] or not server['join_leave_logs']['extended'] \
                or message.author == ClientUser:
            return
        fields = [['Channel', f'<#{message.channel.id}>'], ['Message', message.content]]
        for attachment in message.attachments:
            fields.append(["Attachment URL", attachment.proxy_url])
        await write_embed(server['modlog_id'], message.author, server['join_leave_logs']['leave_color'],
                          f'{message.author.name}#{message.author.discriminator}', 'Message edited.', fields=fields)


def setup(bot):
    bot.add_cog(ModLog(bot))
