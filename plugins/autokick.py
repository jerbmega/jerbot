# This plugin handles automatic kicking of new accounts. Added by request from the Isaac server.

import hikari
import lightbulb
import datetime

import main


def get_enabled_guilds():
    main.load_plugin_configs("autokick", plugin.d)
    return tuple(plugin.d["config"].keys())


plugin = lightbulb.Plugin("Autokick", include_datastore=True)


@plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.KICK_MEMBERS))
@lightbulb.command(
    "autokick",
    "Automatically kicks new accounts (< 7 days old). Please use with caution.",
    guilds=get_enabled_guilds(),
)
@lightbulb.implements(lightbulb.SlashCommand)
async def autokick(ctx: lightbulb.Context) -> None:

    plugin.d["config"][ctx.guild_id]["enabled"] = not plugin.d["config"][ctx.guild_id][
        "enabled"
    ]
    await ctx.respond(
        f"Automatic kicking of new users is now {'enabled' if plugin.d['config'][ctx.guild_id]['enabled'] else 'disabled'}."
    )


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    if (
        event.guild_id in plugin.d["config"]
        and plugin.d["config"][event.guild_id]["enabled"]
    ):
        account_age = event.member.joined_at.replace(
            microsecond=0
        ) - event.user.created_at.replace(microsecond=0)
        if account_age.days <= 7:
            await event.user.kick()


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
