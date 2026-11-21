import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from .. import config
from ..utils import clean, is_whitelisted
from ..views import unban_view


log = logging.getLogger("sinner.honeypot")


WARNING_MARKER = "Sinner - HONEYPOT WARNING"


class Honeypot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ready_done = False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.channel.id != config.HONEYPOT_ID:
            return
        if message.author.id == self.bot.user.id:
            return

        guild = message.guild
        author = message.author

        if not message.webhook_id and is_whitelisted(author):
            return

        content = message.content or "*(aucun texte : pièce jointe / embed)*"
        if message.attachments:
            content += "\n" + "\n".join(a.url for a in message.attachments)

        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            log.error("Suppression impossible: %s", e)

        banned = False
        if message.webhook_id:
            status = "WARNING : Message of **webhook** deleted (not bannable). Check for the Webhooks of the channel"
            color = discord.Color.orange()
        else:
            try:
                await guild.ban(
                    author,
                    reason="Sinner : message send in the Honeypot",
                    delete_message_seconds=config.DELETE_HISTORY,
                )
                status = "INFO : User **Banned** (Recent messages deleted)",
                color = discord.Color.red()
                banned = True
            except discord.Forbidden:
                status = ("ERROR : **Ban impossible** : Insufficient permission or superior role than the bot. Manual action needed")
                color = discord.Color.dark_red()
            except discord.HTTPException as e:
                status = "ERROR : An issue appears : {e}"
                color = discord.Color.dark_red()

        log.info("Honeypot triggered by %s (%s) : %s", author, author.id, status)
        await self._alert(guild, author, content, status, color, banned)


    async def _alert(self, guild, author, content, status, color, banned):
        admin = guild.get_channel(config.ADMIN_ID)
        if admin is None:
            log.warning("Admin Channel not found (ADMIN_CHANNEL_ID in .env file)")
            return

        embed = discord.Embed(title="Honeypot triggered", description=status,
                              color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="User", value=f"{author.mention}\n`{author}` (`{author.id}`)", inline=True)
        embed.add_field(name="Account created", value=discord.utils.format_dt(author.created_at, "R"), inline=True)
        if isinstance(author, discord.Member) and author.joined_at:
            embed.add_field(name="As join", value=discord.utils.format_dt(author.joined_at, "R"), inline=True)
        embed.add_field(name="Message", value=f"```{clean(content)}```", inline=False)
        embed.set_thumbnail(url=author.display_avatar.url)
        embed.set_footer(text="Sinner")

        await admin.send(
            embed=embed,
            view=unban_view(author.id) if banned else None,
            allowed_mentions=discord.AllowedMentions.none(),
        )


    async def ensure_warning_message(self, guild: discord.Guild):
        """Put a warning message in the Honyepot channel"""
        channel = guild.get_channel(config.HONEYPOT_ID)
        if channel is None:
            return
        perms = channel.permissions_for(guild.me)
        if not (perms.view_channel and perms.send_messages):
            log.warning("[%s] Can't post the warning in the channel (permissions).", guild.name)
            return

        async for msg in channel.history(limit=50):
            if msg.author.id == guild.me.id and msg.embeds and msg.embeds[0].footer.text == WARNING_MARKER:
                return

        embed = discord.Embed(
            title="⚠️ WARNING — PLEASE READ CAREFULLY!",
            description=(
                "TYPING HERE = AUTOMATICALLY BAN.\n\n"
                "DO NOT TRY TO BE FUNNY AND TYPE IN THERE. YOU WILL BE AUTOMATICALLY BANNED.\n"
                "THIS IS TO STOP BOTS / SPAMMERS FROM JOINING THE SERVER"
            ),
            color=discord.Color.red(),
        )
        embed.set_footer(text=WARNING_MARKER)
        msg = await channel.send(embed=embed)
        try:
            await msg.pin()
        except discord.HTTPException:
            log.warning("[%s] Warning message is not pinned (permissions).", guild.name)


    @commands.Cog.listener()
    async def on_ready(self):
        if self._ready_done:
            return
        self._ready_done = True

        for guild in self.bot.guilds:
            for cid, name in ((config.HONEYPOT_ID, "honeypot"), (config.ADMIN_ID, "admin")):
                ch = guild.get_channel(cid)
                if ch is not None and not ch.permissions_for(guild.me).view_channel:
                    log.warning("[%s] The bot don't see the channel %s", guild.name, name)
            if guild.get_channel(config.HONEYPOT_ID):
                if not guild.me.guild_permissions.ban_members:
                    log.warning("[%s] Permission « Ban members » missing", guild.name)
                if config.AUTO_WARNING:
                    try:
                        await self.ensure_warning_message(guild)
                    except discord.HTTPException as e:
                        log.warning("[%s] Warning not posted: %s", guild.name, e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Honeypot(bot))