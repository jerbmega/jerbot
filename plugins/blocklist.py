# This plugin handles parsing and deleting of blocklisted words or phrases.

import fluxer
from fluxer import Cog

import re
import wordninja

from thefuzz import utils
from thefuzz.fuzz import token_sort_ratio
from thefuzz.process import extractOne
from datetime import datetime
import decancer_py as decancer

import main

config = {}


class Blocklist(Cog):
    def __init__(self, bot):
        super().__init__(bot)

    async def log_embed(
        self,
        content: str = None,
        guild_id: int = None,
        user: fluxer.User = None,
        channel: fluxer.Channel = None,
    ):
        embed = fluxer.Embed(
            title="Filter tripped (automatically deleted).",
            color=config[guild_id]["log_color"],
            thumbnail=user.avatar_url,
            timestamp=int(
                datetime.now().timestamp()  # Of note, these don't appear to display yet in Fluxer.
            ),
        )
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Message", value=content, inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        return embed

    async def is_blocklisted(self, message: fluxer.Message):
        if "exempt_roles" in config[message.guild_id]:
            for role in (
                await (await self.bot.fetch_guild(message.guild_id)).fetch_member(
                    message.author.id
                )
            ).roles:
                if role in config[message.guild_id]["exempt_roles"]:
                    return False

        # Perform preliminary filtration with decancer, remove whitespace from the entire sentence, reconstruct it into words with wordninja
        # This avoids any attempts to dodge the filter via whitespace or unicode variation
        if "triggers" in config[message.guild_id]:
            content = re.sub(
                r"[^a-zA-Z0-9]",
                "",
                str(decancer.parse(message.content)),
                flags=re.UNICODE,
            )
            content = wordninja.split(content)
            for word in content:
                if utils.full_process(word):
                    match = extractOne(
                        word,
                        config[message.guild_id]["triggers"],
                        scorer=token_sort_ratio,
                    )
                    if match[1] >= 90:
                        return True

        # Next, process any regex filters if applicable
        if "regex_triggers" in config[message.guild_id]:
            for trigger in config[message.guild_id]["regex_triggers"]:
                if re.search(
                    trigger,
                    re.sub(
                        r"\s+",
                        "",
                        message.content.lower(),
                        flags=re.UNICODE,
                    ),
                    flags=re.UNICODE,
                ):
                    return True
        return False

    async def check_blocklist(self, message: fluxer.Message):
        if await self.is_blocklisted(message):
            await message.delete()

            # TODO: implement DM's once implemented in fluxer.py
            await (
                await self.bot.fetch_channel(config[message.guild_id]["channel"])
            ).send(
                embed=await self.log_embed(
                    content=message.content,
                    guild_id=message.guild_id,
                    user=message.author,
                    channel=message.channel,
                )
            )

    @Cog.listener()
    async def on_message(self, message):
        if (
            message.guild_id in config
            and message.content is not None
            and not message.author.bot
        ):
            await self.check_blocklist(message)

    @Cog.listener()
    async def on_message_edit(self, message):
        if (
            message.guild_id in config
            and not message.content is not None
            and not message.author.bot
        ):
            await self.check_blocklist(message)


async def setup(bot):
    global config
    await bot.add_cog(Blocklist(bot))
    config = main.load_plugin_config("blocklist")
