from discord import ClientUser, Embed, channel, member
from discord.ext import commands
from modules.util import config


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def write_embed(self, channel: channel, member: member, color, event, avatar=True, footer=None, fields=None):
        """
        :param channel: ID of the channel to send the log embed in.
        :param member: Member that is being referenced in this embed.
        :param color: Color of the embed.
        :param event: Event that is triggering the embed write: Member Joined, Member Left, Member Banned, etc.
        :param avatar: If avatar should be displayed in moderation logs. Default: True
        :param fields: Optional. [[title, content]]
        :param footer: Optional. Footer for the embed.
        """
        if fields is None:
            fields = []
        embed = Embed(color=color, title=f'{member.name}#{member.discriminator}')
        embed.set_author(name=event)
        if avatar:
            embed.set_thumbnail(url=member.avatar_url if member.avatar_url else member.default_avatar_url)
        if fields:
            for field in fields:
                embed.add_field(name=field[0], value=field[1], inline=True)
        if footer:
            embed.set_footer(text=footer)
        await self.bot.get_channel(channel).send(embed=embed)

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
        await self.write_embed(server['modlog_id'], member, color, 'Member joined.', fields=fields)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        server = config[str(member.guild.id)]
        if not server['join_leave_logs']['enabled']:
            return
        fields = [['User ID', member.id], ['Nickname', member.nick]]
        await self.write_embed(server['modlog_id'], member, server['join_leave_logs']['leave_color'], 'Member left.',
                               fields=fields)

    @commands.Cog.listener()
    async def on_member_ban(self, member):
        server = config[str(member.guild.id)]
        if not server['join_leave_logs']['enabled']:
            return
        await self.write_embed(server['modlog_id'], member, server['join_leave_logs']['leave_color'], 'Member banned.')

    @commands.Cog.listener()
    async def on_message_edit(self, message, new_message):
        server = config[str(message.guild.id)]
        if not server['join_leave_logs']['enabled'] or not server['join_leave_logs']['extended'] \
                or message.author == ClientUser or message.content == new_message.content:
            return
        fields = [['Channel', f'<#{message.channel.id}>'], ['Before', message.content], ['After', new_message.content]]
        for attachment in new_message.attachments:
            fields.append(["Attachment URL", attachment.proxy_url])
        await self.write_embed(server['modlog_id'], message.author, server['join_leave_logs']['leave_color'],
                               'Message edited.', fields=fields)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        server = config[str(message.guild.id)]
        if not server['join_leave_logs']['enabled'] or not server['join_leave_logs']['extended'] \
                or message.author == ClientUser:
            return
        fields = [['Channel', f'<#{message.channel.id}>'], ['Message', message.content]]
        for attachment in message.attachments:
            fields.append(["Attachment URL", attachment.proxy_url])
        await self.write_embed(server['modlog_id'], message.author, server['join_leave_logs']['leave_color'],
                               'Message edited.', fields=fields)


def setup(bot):
    bot.add_cog(ModLog(bot))
