import discord

from . import config


NO_PING = discord.AllowedMentions.none()


class UnbanButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"sinner:unban:(?P<id>[0-9]+)",
):

    def __init__(self, user_id: int):
        super().__init__(
            discord.ui.Button(
                label="Unban user",
                style=discord.ButtonStyle.success,
                emoji="🏳️",
                custom_id=f"sinner:unban:{user_id}",
            )
        )
        self.user_id = user_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match):
        return cls(int(match["id"]))

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("Insufficient permission", ephemeral=True)
        try:
            await interaction.guild.unban(
                discord.Object(id=self.user_id),
                reason=f"Sinner : unban by {interaction.user}",
            )
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            return await interaction.response.send_message(f"Failure : {e}", ephemeral=True)
        self.item.disabled = True
        view = discord.ui.View(timeout=None)
        view.add_item(self.item)
        await interaction.response.edit_message(view=view)
        await interaction.followup.send(f"<@{self.user_id}> unban by {interaction.user.mention}",
            allowed_mentions=NO_PING)


def unban_view(user_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(UnbanButton(user_id))
    return view


_JOIN_BUTTONS = {
    "ban": ("Ban", discord.ButtonStyle.danger, "🔨", "ban_members"),
    "kick": ("Kick", discord.ButtonStyle.secondary, "🚫", "kick_members"),
    "ignore": ("Ignore", discord.ButtonStyle.success, "🔇", "ignore_members")
}


class JoinActionButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"sinner:join(?Paction>ban|kick|ignore):(?P<id>[0-9]+)",
):
    def __init__(self, action: str, user_id: int, disabled: bool = False):
        label, style, emoji, _ = _JOIN_BUTTONS[action]
        super().__init__(
            discord.ui.Button(
                label=label,
                style=style,
                emoji=emoji,
                custom_id=f"sinner:join:{action}:{user_id}",
                disabled=disabled,
            )
        )
        self.action = action
        self.user_id = user_id


    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match):
        return cls(match["action"], int(match["id"]))

    async def callback(self, interaction: discord.Interaction):
        perm = _JOIN_BUTTONS[self.action][3]
        if not getattr(interaction.user.guild_permissions, perm, False):
            return await interaction.response.send_message("Insufficient Permissions", ephemeral=True)

        guild = interaction.guild
        announce = None
        if self.action == "ban":
            try:
                await guild.ban(
                    discord.Object(id=self.user_id),
                    reason=f"Sinner : Banned by {interaction.user}",
                    delete_message_seconds=config.DELETE_HISTORY,
                )
            except discord.HTTPException as e:
                return await interaction.response.send_message(f"Ban Failed : {e}", ephemeral=True)
            announce = f"INFO <@{self.user_id}> banned by {interaction.user.mention}."
        elif self.action == "kick":
            member = guild.get_member(self.user_id)
            if member is None:
                return await interaction.response.send_message("User not found.", ephemeral=True)
            try:
                await member.kick(reason=f"Sinner : kicked by {interaction.user}")
            except discord.HTTPException as e:
                return await interaction.response.send_message(f"Échec du kick : {e}", ephemeral=True)
            announce = f"INFO <@{self.user_id}> kicked by {interaction.user.mention}."

        await interaction.response.edit_message(view=join_view(self.user_id, disabled=True))
        if announce:
            await interaction.followup.send(announce, allowed_mentions=NO_PING)


def join_view(user_id: int, disabled: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for action in _JOIN_BUTTONS:
        view.add_item(JoinActionButton(action, user_id, disabled))
    return view
