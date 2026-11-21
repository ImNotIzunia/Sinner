import discord
from . import config


def clean(text: str, limit: int = 1000) -> str:
    text = text.replace("```", "'''")
    return text if len(text) <= limit else text[:limit] + "..."


def is_whitelisted(user: discord.abc.User) -> bool:
    if user.id in config.WHITELIST_USERS:
        return True
    if isinstance(user, discord.Member):
        if user.id == user.guild.owner_id:
            return True
        if any(role.id in config.WHITELIST_ROLES for role in user.roles):
            return True
    return False


