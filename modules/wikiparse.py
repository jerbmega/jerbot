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
    async def wiki(self, ctx, *, parse: str):
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

def setup(bot):
    bot.add_cog(WikiParse(bot))
