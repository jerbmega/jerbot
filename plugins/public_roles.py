# This plugin handles joining and leaving of public roles.

import hikari
import lightbulb
import miru

import main
import err


def get_enabled_guilds():
    main.load_plugin_configs("public_roles", plugin.d)
    return tuple(plugin.d["config"].keys())


plugin = lightbulb.Plugin("Public Roles", include_datastore=True)


class AddRoleButton(miru.Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def callback(self, ctx: miru.Context) -> None:
        await ctx.app.rest.add_role_to_member(ctx.guild_id, ctx.user, self.role_id)
        self.view.success = True
        self.view.stop()


class DelRoleButton(miru.Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def callback(self, ctx: miru.Context) -> None:
        await ctx.app.rest.remove_role_from_member(ctx.guild_id, ctx.user, self.role_id)
        self.view.success = True
        self.view.stop()


@plugin.command
@lightbulb.command("join", "Join a public role", guilds=get_enabled_guilds())
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    view = miru.View()

    roles = ctx.bot.cache.get_roles_view_for_guild(ctx.guild_id)
    for id in plugin.d["config"][ctx.guild_id]:
        button = AddRoleButton(style=hikari.ButtonStyle.PRIMARY, label=roles[id].name)
        button.role_id = id
        view.add_item(button)

    message = await (
        await ctx.respond(
            "Choose a role to join.",
            components=view.build(),
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    )
    view.start(message)
    await view.wait()

    if hasattr(view, "success"):
        await ctx.edit_last_response(
            "You have been added to the requested role.", components=None
        )
    else:
        await ctx.edit_last_response("You didn't respond in time!", components=None)


@plugin.command
@lightbulb.command("leave", "Leave a public role", guilds=get_enabled_guilds())
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    view = miru.View()

    roles = ctx.bot.cache.get_roles_view_for_guild(ctx.guild_id)
    user_roles = ctx.member.role_ids

    for id in plugin.d["config"][ctx.guild_id]:
        if id in user_roles:
            button = DelRoleButton(
                style=hikari.ButtonStyle.PRIMARY, label=roles[id].name
            )
            button.role_id = id
            view.add_item(button)

    if len(view.children) == 0:
        raise err.NoPublicRoles

    message = await ctx.respond(
        "Choose a role to leave.",
        components=view.build(),
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    view.start(await message)
    await view.wait()

    if hasattr(view, "success"):
        await ctx.edit_last_response(
            "You have been removed from the requested role.", components=None
        )
    else:
        await ctx.edit_last_response("You didn't respond in time!", components=None)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
