import discord


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
        await interaction.followup.send(f"<@{self.user_id}> unban by {interaction.user.mention}")


def unban_view(user_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(UnbanButton(user_id))
    return view


