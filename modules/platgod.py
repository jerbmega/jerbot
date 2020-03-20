from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import modules.db as db
from modules.util import config, write_embed


class PlatGod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # this command is only for the isaac server
    async def cog_check(self, ctx):
        return ctx.guild.id == 123641386921754625

    @commands.command()
    async def platgod(self, ctx, *, parse: str):
        """
        Fetches a result from Platinum God. Only works in the Isaac server.
        Syntax: platgod (page = [wotl/vanilla, rb/rebirth, ab/afterbirth, anti/antibirth], optional) [query]
        """
        parse = parse.split(' ', 1)
        original = ["wotl", "vanilla"]
        rebirth = ["rb", "rebirth"]
        afterbirth = ["ab", "afterbirth"]
        anti = ["anti", "antibirth"]
        page = "original" if parse[0] in original else "rebirth" if parse[0] in rebirth \
            else "afterbirth" if parse[0] in afterbirth else "antibirth" if parse[0] in anti else "afterbirthplus"
        parse = ' '.join(parse) if page == "afterbirthplus" else parse[1]
        items = db.query(f'select distinct item from platgod_{page} where item like "%{parse}%"')
        if not items:
            await ctx.send("No results found.")
            return
        fields = [[items[0], "\n".join(db.query(f'select detail from platgod_{page} where item ="{items[0]}"')[1:])]]

        embed = await write_embed(ctx.channel.id, None, config['main']['embed_color'], f"1/{len(items)}",
                                  f"Search results for {parse} [{page}]", fields=fields, avatar=False)
        if len(items) > 1:
            await embed.add_reaction("⬅️")
            await embed.add_reaction("➡️")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return

        for embed in reaction.message.embeds:
            if "Search results for" in embed.author.name:
                page = embed.title.split("/")
                page = [int(page[0]), int(page[1])]
                page[0] = page[0] - 1 if reaction.emoji == '⬅️' else page[0] + 1 if reaction.emoji == "➡️" else page[0]
                page[0] = page[1] if page[0] < 1 else 1 if page[0] > page[1] else page[0]
                embed.title = f'{page[0]}/{page[1]}'
                embed.clear_fields()
                item = embed.author.name.split("Search results for ")[1].split(" [")[0]
                ver = embed.author.name.split("[")[1][:-1]
                items = db.query(f'select distinct item from platgod_{ver} '
                                 f'where item like "%{item}%"')
                embed.add_field(name=items[page[0] - 1], value="\n".join(
                    db.query(f'select detail from platgod_{ver} where item ="{items[page[0] - 1]}"')[1:]))
                await reaction.message.edit(embed=embed)
                await reaction.message.remove_reaction(reaction.emoji, user)

    @commands.command()
    @commands.is_owner()
    async def fetch_platgod(self, ctx):
        """
        Updates the copy of Platinum God stored in the database. Owner only.
        """
        base_message = await ctx.send("Beginning loop.")
        platgods = ['original', 'rebirth', 'antibirth', 'afterbirth', 'afterbirth-plus']
        for base_url in platgods:
            await base_message.edit(content=f"Fetching...")
            soup = BeautifulSoup(requests.get(f"https://platinumgod.co.uk/{base_url}").content, 'html.parser')
            items = soup.find(class_="main").find_all(class_="item-title")
            db.drop_table(f'platgod_{base_url.replace("-", "")}')
            db.try_create_table(f'platgod_{base_url.replace("-", "")}', ('item', 'detail'))
            await base_message.edit(content=f"Saving {base_url} to database.")
            for item in items:
                item_title = item.text
                details = item.parent.find_all("p")
                for detail in details:
                    if "tags" not in str(detail) and str(detail) :
                        if not "birth Pills" in item_title.replace("+", ""):
                            print(f'{base_url} insert into platgod_{base_url.replace("-", "")} values (?, ?)',
                                     (item_title, detail.text))
                            db.c.execute(f'insert into platgod_{base_url.replace("-", "")} values (?, ?)',
                                     (item_title, detail.text))

                db.conn.commit()
        await base_message.edit(content="Finished.")


def setup(bot):
    bot.add_cog(PlatGod(bot))
