from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import modules.db as db
import discord.member


class WikiParse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # this command is only for the isaac server
    async def cog_check(self, ctx):
        return ctx.guild.id == 123641386921754625

    @commands.command()
    async def wiki_neo(self, ctx, *, parse: str):
        """
        Fetches a result from the Antibirth, Revelations or Isaac Gamepedia. Only works in the Isaac server.
        Syntax: wiki (wiki = [anti/antibirth, rev/revelations], optional) [query]
        """
        parse = parse.split(' ', 1)
        anti = ["antibirth", "anti"]
        rev = ["revelations", "rev"]
        subdomain = "antibirth" if parse[0] in anti else "tboirevelations" if parse[0] in rev \
            else "bindingofisaacrebirth"
        parse = ' '.join(parse) if subdomain == "bindingofisaacrebirth" else parse[1]
        page = requests.get(f"https://{subdomain}.gamepedia.com/index.php?search={parse}")
        message = f"I couldn't find an exact match. Here is a link to this query's search page. {page.url}" \
            if "search" in page.url else page.url
        await ctx.send(message)


    @commands.command()
    async def platgod_neo(self, ctx, *, parse: str):
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
        response = db.query(f'select detail from platgod_{page} where item like "%{parse}%"')
        response[0] = f'**{response[0]}**'
        try:
            await ctx.send('\n'.join(response))
        except discord.HTTPException:
            await ctx.send("This query is too broad. Please try again.")

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
                        print(f'{base_url} insert into platgod_{base_url.replace("-", "")} values (?, ?)',
                                     (item_title, detail.text))
                        db.c.execute(f'insert into platgod_{base_url.replace("-", "")} values (?, ?)',
                                     (item_title, detail.text))

                db.conn.commit()
        await base_message.edit(content="Finished.")


def setup(bot):
    bot.add_cog(WikiParse(bot))
