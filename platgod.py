# This plugin handles fetching information Platinum God, a concise but less accurate source of information about the game.

import hikari
import miru
import lightbulb
import subprocess
import sys
import aiohttp
from thefuzz.fuzz import token_sort_ratio
from thefuzz.process import extract

import main
import db

# Doing it this way since I really don't want to have people need to make a custom image just for a silly little plugin
try:
    import bs4
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    import bs4


def get_enabled_guilds():
    main.load_plugin_configs("platgod", plugin.d)
    return tuple(plugin.d["config"].keys())


plugin = lightbulb.Plugin("Platinum God", include_datastore=True)


async def platgod_embed(
    color: str = None,
    query: str = None,
    page: str = None,
    page_num: int = None,
):
    embed = hikari.embeds.Embed(
        title=query[page_num - 1][0],
        color=color,
    )
    embed.set_author(name=f'Platinum God - {page.replace("_", " ").capitalize()}')

    embed.set_footer(
        text=f"Potential match {page_num} of 10 - Can't find your item? Try again with a different query."
    )

    for detail in await db.queryall(
        "bos_platgod",
        f'select detail from {page} where item = "{query[page_num - 1][0]}"',
    ):
        if not embed.description:
            embed.description = detail
        else:
            embed.description = embed.description + f"\n\n{detail}"
    return embed


class PlatgodView(miru.View):
    @miru.button(label="Previous", style=hikari.ButtonStyle.PRIMARY)
    async def prev_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if self.pagenum > 1:
            self.pagenum = self.pagenum - 1
            await ctx.edit_response(
                embed=await platgod_embed(
                    plugin.d["config"][ctx.guild_id]["embed_color"],
                    self.query,
                    self.page,
                    self.pagenum,
                )
            )

    @miru.button(label="Next", style=hikari.ButtonStyle.PRIMARY)
    async def next_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if self.pagenum < 10:
            self.pagenum = self.pagenum + 1
            await ctx.edit_response(
                embed=await platgod_embed(
                    plugin.d["config"][ctx.guild_id]["embed_color"],
                    self.query,
                    self.page,
                    self.pagenum,
                )
            )


# This is one of the only pieces of code left over from V3 (although adapted to Hikari and cleaned up a bit, of course)...
# The scraping works, this is infrequently ran, might as well reuse it
@plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command(
    "fetch_platgod",
    "Rescrapes the latest version of Platinum God into the database",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def fetch_platgod(ctx: lightbulb.Context) -> None:
    response = None

    for _, platgod in enumerate(plugin.d["config"][ctx.guild_id]["pages"], start=1):
        async with aiohttp.ClientSession() as session:
            response_text = f"Working on {platgod}... [{_}/{len(plugin.d['config'][ctx.guild_id]['pages'])}]"
            if not response:
                response = await ctx.respond(
                    response_text,
                    flags=hikari.MessageFlag.EPHEMERAL,
                )
            else:
                await ctx.edit_last_response(response_text)
            async with session.get(f"https://platinumgod.co.uk/{platgod}") as resp:
                platgod = platgod.replace("-", "_")
                resp = await resp.text()
                soup = bs4.BeautifulSoup(resp, "html.parser")
                items = soup.find(class_="main").find_all(class_="item-title")
                await db.drop_table("bos_platgod", platgod)
                await db.create_table("bos_platgod", platgod, ("item", "detail"))

                for item in items:
                    title = item.text
                    for detail in item.parent.find_all("p")[
                        1:-1
                    ]:  # First element of list is just the item name again, last is tags which are useless
                        await db.insert(
                            "bos_platgod",
                            platgod,
                            "(?,?)",
                            (title, detail.text),
                        )
    await ctx.edit_last_response("Done.")


# Even though Book of Secrets is explicitly designed for the Isaac server, I still don't want to hardcode anything.
# We're using custom autocomplete so I can return a list of values specific to every server.
@plugin.command
@lightbulb.option(
    "page",
    "Page of Platinum God to check",
    default="repentance",
    required=False,
    autocomplete=True,
)
@lightbulb.option("query", "Query to run against Platinum God")
@lightbulb.command(
    "platgod", "Check Platinum God for information", guilds=get_enabled_guilds()
)
@lightbulb.implements(lightbulb.SlashCommand)
async def platgod(ctx: lightbulb.Context) -> None:
    view = PlatgodView()
    view.page = ctx.options.page.replace("-", "_")
    view.pagenum = 1

    items = await db.queryall("bos_platgod", f"select distinct item from {view.page}")
    view.query = extract(ctx.options.query, items, scorer=token_sort_ratio, limit=10)

    embed = await platgod_embed(
        plugin.d["config"][ctx.guild_id]["embed_color"],
        view.query,
        view.page,
        view.pagenum,
    )
    message = await ctx.respond(components=view, embed=embed)

    ctx.bot.d.miru.start_view(view)
    await view.wait()

    embed = (await ctx.previous_response).embeds[0]
    embed.set_footer("Interaction has timed out.")
    await ctx.edit_last_response(embed=embed, components=None)


@platgod.autocomplete("page")
async def platgod_autocomplete(option, interaction):
    pages = plugin.d["config"][interaction.guild_id]["pages"]
    return [page for page in pages if option.value in page]


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
