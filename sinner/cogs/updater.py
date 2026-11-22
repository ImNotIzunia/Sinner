import asyncio
import logging
import re

import aiohttp
import discord
from discord.ext import commands, tasks

from .. import GITHUB_REPO, __version__, config, state
from ..utils import clean
from ..views import NO_PING


log = logging.getLogger("sinner.updater")


API_URL = "https://api.github.com/repos/ImNotIzunia/Sinner/releases/latest"


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.match(r"\s*v?(\d+(?:\.\d+)*)", text or "")
    if not match:
        return None
    parts = [int(p) for p in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


async def fetch_latest_release(repo: str) -> dict | None:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"Sinner/{__version__}"}
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(API_URL.format(repo=repo)) as resp:
                if resp.status == 404:
                    log.info("No release uploaded in %s.", repo)
                    return None
                if resp.status in (403, 429):
                    log.warning("Request limit : retry in the next cycle.")
                    return None
                if resp.status != 200:
                    log.warning("GitHub answers %s at the verification of the update.", resp.status)
                    return None
                return await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        log.warning("Update checker impossible : %s", e)
        return None


class Updater(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = GITHUB_REPO

    async def cog_load(self):
        if not config.UPDATE_CHECK:
            return
        self.check_updates.change_interval(hours=config.UPDATE_CHECK_HOURS)
        self.check_updates.start()

    async def cog_unload(self):
        self.check_updates.cancel()


    @tasks.loop(hours=6)
    async def check_updates(self):
        await self.check_once()

    @check_updates.before_loop
    async def _wait_ready(self):
        await self.bot.wait_until_ready()

    @check_updates.error
    async def _on_error(self, error: BaseException):
        log.warning("Error at the update verification : %s", error)


    async def check_once(self) -> bool:
        release = await fetch_latest_release(self.repo)
        if not release:
            return False

        tag = release.get("tag_name") or ""
        remote, local = parse_version(tag), parse_version(__version__)
        if remote is None or local is None or remote <= local:
            return False

        data = state.load()
        if data.get("last_notified") == tag:
            return False

        if await self._notify(release, tag):
            data["last_notified"] = tag
            state.save(data)
            return True
        return False


    async def _notify(self, release: dict, tag: str) -> bool:
        url = release.get("html_url") or ""
        if not url.startswith("https://github.com/"):
            url = f"https://github.com/{self.repo}/releases"

        embed = discord.Embed(
            title="🆕 New update of `Sinner` Available",
            description=f"Version installée : **{__version__}**\nNouvelle version : **{tag}**",
            url=url,
            color=discord.Color.blurple(),
        )
        notes = (release.get("body") or "").strip()
        if notes:
            embed.add_field(name=release.get("name") or tag, value=clean(notes, 900), inline=False)
        embed.add_field(
            name="How to update the bot",
            value="```\ngit pull\npip install -r requirements.txt\n```then restart the bot.",
            inline=False,
        )
        embed.set_footer(text="Sinner • The bot is not updated automatically")

        sent = False
        for guild in self.bot.guilds:
            channel = guild.get_channel(config.ADMIN_ID)
            if channel is None:
                continue
            try:
                await channel.send(embed=embed, allowed_mentions=NO_PING)
                sent = True
            except discord.HTTPException as e:
                log.warning("[%s] Update notification not send : %s", guild.name, e)
        return sent


async def setup(bot: commands.Bot):
    await bot.add_cog(Updater(bot))
