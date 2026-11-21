import logging
import discord
from discord.ext import commands

from . import __version__, config
from .views import JoinActionButton, UnbanButton


log = logging.getLogger("sinner")


EXTENSIONS = [
    "sinner.cogs.honeypot",
    "sinner.cogs.profiling",
    "sinner.cogs.updater",
]


class Sinner(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = config.PROFILING
        intents.invites = config.PROFILING
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)

    async def setup_hook(self):
        self.add_dynamic_items(UnbanButton, JoinActionButton)
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            log.info("Extension Downloaded : %s", ext)

    async def on_ready(self):
        log.info("Sinner is connected as %s (%s)", self.user, self.user.id)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        await super().on_command_error(ctx, error)


