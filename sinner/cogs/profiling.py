import logging
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from .. import config
from ..views import NO_PING, join_view


log = logging.getLogger("sinner.profiling")


SUSPICIOUS_NAME = re.compile(
    r"(discord\.gg|https?://|\.gg/|nitro|free\s?gift|airdrop|crypto|giveaway|onlyfans|18\+|telegram|t\.me)",
    re.IGNORECASE,
)

DIGIT_TAIL = re.compile(r"\d{4,}$")


def humanize(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds} s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    if hours < 48:
        return f"{hours} h {minutes} min"
    days = hours // 24
    if days < 60:
        return f"{days} jours"
    return f"{days // 30} mois ({days} jours)"


def profile_member(member, join_count: int = 1) -> tuple[int, list[str], list[str]]:
    now = datetime.now(timezone.utc)
    age = now - member.created_at
    score = 0
    bad: list[str] = []
    good: list[str] = []

    # Âge du compte : critère le plus fiable
    if age < timedelta(days=1):
        score += 40
        bad.append("Account created **less than 24 h**")
    elif age < timedelta(days=7):
        score += 25
        bad.append("Account created **less than 7 jours**")
    elif age < timedelta(days=30):
        score += 10
        bad.append("Account created **less than 30 jours**")
    elif age > timedelta(days=365):
        good.append("Account with a complete year")

    if member.joined_at and (member.joined_at - member.created_at) < timedelta(minutes=10):
        score += 15
        bad.append("Join **less than 10 min** after account creation")

    if member.avatar is None:
        score += 10
        bad.append("Default picture")
    else:
        good.append("Custom picture")
    if member.public_flags.value == 0:
        score += 5
        bad.append("No Discord Badges")
    else:
        good.append("Have Discord Badges")

    # Pseudo
    if SUSPICIOUS_NAME.search(f"{member.name} {member.global_name or ''}"):
        score += 30
        bad.append("Pseudo with a **suspicious name**")
    if DIGIT_TAIL.search(member.name):
        score += 10
        bad.append("Pseudo ending with a long string of numbers")

    # Raid
    if join_count >= config.RAID_JOINS:
        score += 20
        bad.append(f"**Possible Raid** : {join_count} arrived in {config.RAID_WINDOW} s")

    if member.bot:
        bad.append("Account marked as a **BOT**")

    return min(score, 100), bad, good


def risk_level(score: int) -> tuple[str, discord.Color]:
    if score >= 70:
        return "🔴 Highly suspect", discord.Color.red()
    if score >= 45:
        return "🟠 Suspect", discord.Color.orange()
    if score >= 20:
        return "🟡 To watch", discord.Color.gold()
    return "🟢 Mostly safe", discord.Color.green()


class Profiling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recent_joins: dict[int, deque] = defaultdict(deque)
        self.invite_cache: dict[int, dict[str, int]] = {}

    async def _cache_invites(self, guild: discord.Guild):
        try:
            self.invite_cache[guild.id] = {i.code: i.uses or 0 for i in await guild.invites()}
        except discord.Forbidden:
            self.invite_cache.pop(guild.id, None)

    async def _find_invite(self, guild: discord.Guild) -> str:
        old = self.invite_cache.get(guild.id)
        if old is None:
            return "Unkown (permission missing)"
        try:
            new_invites = await guild.invites()
        except discord.HTTPException:
            return "Inconnue"
        used = next((i for i in new_invites if (i.uses or 0) > old.get(i.code, 0)), None)
        self.invite_cache[guild.id] = {i.code: i.uses or 0 for i in new_invites}
        if used is None:
            return "Unkown (expired or one shot link)"
        inviter = f" by {used.inviter.mention}" if used.inviter else ""
        return f"`{used.code}`{inviter} ({used.uses} usage)"

    @commands.Cog.listener()
    async def on_ready(self):
        if not config.PROFILING:
            return
        for guild in self.bot.guilds:
            await self._cache_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if config.PROFILING and invite.guild:
            self.invite_cache.setdefault(invite.guild.id, {})[invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if config.PROFILING and invite.guild:
            self.invite_cache.get(invite.guild.id, {}).pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not config.PROFILING:
            return
        guild = member.guild
        admin = guild.get_channel(config.ADMIN_ID)
        if admin is None:
            log.warning("Admin channel not found (ADMIN_CHANNEL_ID).")
            return

        now = datetime.now(timezone.utc).timestamp()
        joins = self.recent_joins[guild.id]
        joins.append(now)
        while joins and now - joins[0] > config.RAID_WINDOW:
            joins.popleft()
        if len(joins) == config.RAID_JOINS:
            await admin.send(f"🚨 **Possible Raid** : {len(joins)} arrived in {config.RAID_WINDOW} s.")

        invite_text = await self._find_invite(guild)
        score, bad, good = profile_member(member, len(joins))
        label, color = risk_level(score)

        embed = discord.Embed(
            title="👤 New user",
            description=f"{member.mention} : **{label}** (score : `{score}/100`)",
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Pseudo", value=f"`{member.name}`\nDisplay : `{member.global_name or '—'}`", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Type", value="🤖 Bot" if member.bot else "Human", inline=True)
        embed.add_field(
            name="Account created",
            value=f"{discord.utils.format_dt(member.created_at, 'F')}\n"
                  f"({humanize(datetime.now(timezone.utc) - member.created_at)})",
            inline=True,
        )
        embed.add_field(
            name="Arrived",
            value=discord.utils.format_dt(member.joined_at or datetime.now(timezone.utc), "T"),
            inline=True,
        )
        embed.add_field(name="Invitation", value=invite_text, inline=True)
        if bad:
            embed.add_field(name="Bad signs", value="\n".join(f"• {b}" for b in bad), inline=False)
        if good:
            embed.add_field(name="Good signs", value="\n".join(f"• {g}" for g in good), inline=False)
        embed.set_footer(text=f"Members : {guild.member_count} • profile score • Sinner")

        await admin.send(embed=embed, view=join_view(member.id), allowed_mentions=NO_PING)


async def setup(bot: commands.Bot):
    await bot.add_cog(Profiling(bot))
