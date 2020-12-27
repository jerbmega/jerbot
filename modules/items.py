from discord.ext import commands
import modules.db as db
from datetime import timedelta
from modules.util import config, schedule_task, remove_task, write_embed
from math import log
from random import randint
from sqlite3 import OperationalError
import discord

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    roles = [
        [["i want to be a demon", "i want to be a devil", "i am a demon", "i am a devil"], 3,
         ":smiling_imp: **The pact is sealed.**", 287682288689348608, 287682181826871299],
        [["i want to be an angel", "i am an angel"], 3, "**:angel: The gates are opened.**",
         287682181826871299, 287682288689348608],
        [["i am a chest boy", "i want to be a chest boy"], 25, "**:gem: Welcome to ascension.**", 766808354156314624, 766806448952573952],
        [["i am a dark boy", "i want to be a dark boy"], 25, "**:black_circle: Welcome to darkness.**", 766806448952573952, 766808354156314624],
        [["i am a golden god", "i want to be a golden god", "i am a piss god", "i want to be a piss god"], 50, "**:yellow_heart: Now stop playing!**",
         287682309795217419],
        [["i am a platinum god", "i want to be a platinum god"], 100, "**:blue_heart: Now stop playing!**", 306938966832316416],
        [["i am a real platinum god", "i want to be a real platinum god", "i'm really a platinum god"], 200, ":white_heart: **Please stop.**", 423231010419769365],
        [["i am an eternal god", "i want to be an eternal god"], 300, ":octagonal_sign: **Stop.**", 358318406778486784]]

    async def evaluate_items(self, user):
        amount = log(db.query(f'select amount from items_progress where user = {user}')[0]) * 5
        progress = db.query(f'select progress from items_progress where user = {user}')[0] + amount
        db.update('items_progress', f'progress = {progress} where user = {user}')
        db.update('items_progress', f'amount = 0 where user = {user}')
        if progress >= 100:
            await self.award_item(user)

    async def award_item(self, user):
        db.update('items_progress', f'progress = 0 where user = {user}')
        db.try_create_table("received_items", ('user', 'dlc', 'item'))
        award_dlcs = db.query(f'select dlc from items where item not in (select item from received_items where user = {user});')
        award_items = db.query(f'select item from items where item not in (select item from received_items where user = {user});')
        award = randint(0, len(award_dlcs) - 1)
        try: # necessary in case the user blocks the bot / has friends-only dm's
            await discord.utils.get(self.bot.users, id=user).send(f":crown: You just found {award_items[award]}!\n")
        except:
            pass
        await self.bot.get_channel(193042852819894272).send(f"<@{user}> just found {award_items[award]}!")
        db.insert("received_items", (user, award_dlcs[award], award_items[award]))


    @commands.Cog.listener()
    async def on_message(self, message):
        server_id = str(message.guild.id)
        if not message.guild.id == 123641386921754625 or message.author == self.bot.user:
            return

        db.try_create_table('items_progress', ('user', 'amount', 'progress'))
        try:
        #if True:
            db.update('items_progress',
                      f'amount = {db.query(f"select amount from items_progress where user = {message.author.id}")[0] + 1} '
                      f'where user = {message.author.id}')
        except Exception as e:
            print('making new row: {e}')
            db.insert('items_progress', (message.author.id, 1, 0))
        try:
            await remove_task(f"items_{message.author.id}")
        except:
            pass
        await schedule_task(self.evaluate_items, timedelta(minutes=10), f"items_{message.author.id}",
                            [message.author.id])

        if message.channel.id == 294885337262456832 or message.channel.id == 290882932636254210:
            if message.content.lower() == "i am pure":
                for role in self.roles:
                    await message.author.remove_roles(discord.utils.get(message.guild.roles, id=role[3]))
                await message.channel.send("**You are cleansed.**")
            for role in self.roles:
                if message.content.lower() in [text for text in role[0]]:
                    amount = len(db.query(f"select item from received_items where user = {message.author.id}"))
                    roles = message.author.roles
                    try:
                        if role[4] in [role.id for role in roles]:
                            await message.channel.send("You already chose your fate.")
                            return
                    except IndexError:
                        pass
                    if amount >= role[1]:
                        await message.channel.send(role[2])
                        await message.author.add_roles(discord.utils.get(message.guild.roles, id=role[3]))
                    else:
                        await message.channel.send(f"You need **{role[1] - amount}** more items!")

    @commands.command(aliases=["lb", "leaderboard"])
    async def leaderboards(self, ctx):
        if not ctx.guild.id == 123641386921754625: return
        lb = []
        results = db.query('select user as frequency from received_items group by user order by count(*) desc')
        amount = 0
        for i, user in enumerate(results):
            try:
                if amount < 10:
                    lb.append([discord.utils.get(ctx.guild.members, id=user).name,
                               len(db.query(f'select item from received_items where user = {user}'))])
                    amount = amount + 1
            except: #TODO narrow:
                pass
        lb_users = "\n".join(str(user[0]) for user in lb)
        lb_items = "\n".join(str(user[1]) for user in lb)
        fields = [["Users", lb_users], ["Items", lb_items]]
        await write_embed(ctx.channel.id, None, config['main']['embed_color'], "Leaderboards", fields=fields,
                          description=f"The most active, technically.", avatar=False)

    @commands.command()
    async def items(self, ctx):
        if not ctx.guild.id == 123641386921754625: return
        rbitems = [len(db.query(f"select item from received_items where dlc = 'rebirth' and user = {ctx.author.id}")),
                   len(db.query(f"select item from items where dlc = 'rebirth'"))]
        abitems = [len(db.query(f"select item from received_items where dlc = 'afterbirth' and user = {ctx.author.id}")),
                   len(db.query(f"select item from items where dlc = 'afterbirth'"))]
        anbitems = [len(db.query(f"select item from received_items where dlc = 'anti' and user = {ctx.author.id}")),
                   len(db.query(f"select item from items where dlc = 'anti'"))]
        abpitems = [len(db.query(f"select item from received_items where dlc = 'abp' and user = {ctx.author.id}")),
                   len(db.query(f"select item from items where dlc = 'abp'"))]

        total = rbitems[0] + abitems[0] + anbitems[0] + abpitems[0]
        full_total = rbitems[1] + abitems[1] + anbitems[1] + abpitems[1]
        fields = [
            ["Rebirth", f"{rbitems[0]}/{rbitems[1]}"],
            ["Afterbirth", f"{abitems[0]}/{abitems[1]}"],
            ["Afterbirth+", f"{abpitems[0]}/{abpitems[1]}"],
            ["Antibirth", f"{anbitems[0]}/{anbitems[1]}"]
        ]
        await write_embed(ctx.channel.id, None, config['main']['embed_color'], "Collected items", fields=fields,
                          description=f"{total}/{full_total}", footer=f"{full_total - total} to go!", avatar=False)

def setup(bot):
    bot.add_cog(Items(bot))
