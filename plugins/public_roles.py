# This plugin handles parsing and deleting of blocklisted words or phrases.

import fluxer
from fluxer import Cog

import main
import err

config = {}


class PublicRoles(Cog):
    def __init__(self, bot):
        super().__init__(bot)

    # Fluxer.py seems to have no good way to just fetch a single role by ID... so here's a wrapper around fetch_roles.
    async def fetch_public_roles(self, guild: str):
        public_roles = []
        for role in await (await self.bot.fetch_guild(guild)).fetch_roles():
            if role.id in config[guild]:
                public_roles.append(role)
        return public_roles

    # Similarly, Fluxer itself doesn't have a good way to fetch a role's ID, so a command is needed.
    @Cog.command()
    async def fetch_roles(self, ctx, guild: str = None):
        try:
            if not ctx.author.id == main.config["owner"]:
                raise err.InsufficientPermissions

            if not guild:
                guild = ctx.guild_id

            print("---ROLE LIST---")
            for role in await (await self.bot.fetch_guild(guild)).fetch_roles():
                print(f"{role.id} - {role.name}")

            await ctx.reply("Role list sent to stdout.")

        except err.InsufficientPermissions:
            await ctx.reply("You have insufficient permissions to run this command.")
        except fluxer.errors.NotFound:
            await ctx.reply("Invalid guild specified.")

    @Cog.command()
    async def roles(self, ctx):
        await ctx.reply(
            f"Available roles: `{', '.join(role.name for role in (await self.fetch_public_roles(ctx.guild_id)))}`"
        )

    @Cog.command()
    async def join(self, ctx, *, role: str):
        public_roles = await self.fetch_public_roles(ctx.guild_id)

        for public_role in public_roles:
            if role.lower() == public_role.name.lower():
                await (
                    await (await self.bot.fetch_guild(ctx.guild_id)).fetch_member(
                        ctx.author.id
                    )
                ).add_role(
                    public_role.id,
                    reason="User opted in to public role.",
                    guild_id=ctx.guild_id,  # This API is stupid. Why is guild_id required if we're running this on a GuildMember object?
                )

                await ctx.reply(
                    f"You have been added to the `{public_role.name}` role."
                )
                return

        await ctx.reply(
            f"That role is not valid or isn't a public role.\nAvailable roles: `{', '.join(role.name for role in public_roles)}`"
        )

    @Cog.command()
    async def leave(self, ctx, *, role: str):
        public_roles = await self.fetch_public_roles(ctx.guild_id)

        for public_role in public_roles:
            if role.lower() == public_role.name.lower():
                await (
                    await (await self.bot.fetch_guild(ctx.guild_id)).fetch_member(
                        ctx.author.id
                    )
                ).remove_role(
                    public_role.id,
                    reason="User opted out of public role.",
                    guild_id=ctx.guild_id,
                )

                await ctx.reply(
                    f"You have been removed from the `{public_role.name}` role."
                )
                return

        await ctx.reply(
            f"That role is not valid or isn't a public role.\nAvailable roles: `{', '.join(role.name for role in public_roles)}`"
        )


async def setup(bot):
    global config
    await bot.add_cog(PublicRoles(bot))
    config = main.load_plugin_config("public_roles")


async def teardown(bot):
    await bot.remove_cog("PublicRoles")
