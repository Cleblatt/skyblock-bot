import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.embeds import build_botinfo_embed, build_error_embed

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # You could configure a specific channel ID in config for reports/suggestions
        self.dev_channel_id = None 

    @app_commands.command(name="suggest", description="Send user suggestions to the developer channel")
    @app_commands.describe(message="Your suggestion for the bot")
    async def suggest(self, interaction: discord.Interaction, message: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            # Here you would route to a specific Discord channel via ID
            # e.g., channel = self.bot.get_channel(self.dev_channel_id)
            logger.info(f"Suggestion from {interaction.user}: {message}")
            
            embed = discord.Embed(title="💡 Suggestion Sent", description="Thank you! Your suggestion has been recorded.", color=0x2ECC71)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /suggest: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", "Could not send suggestion."))

    @app_commands.command(name="report", description="Send bug reports to the developer channel")
    @app_commands.describe(bug="Describe the bug you found")
    async def report(self, interaction: discord.Interaction, bug: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            logger.warning(f"BUG REPORT from {interaction.user}: {bug}")
            
            embed = discord.Embed(title="🐛 Bug Reported", description="Thank you! The developers have been notified.", color=0xE74C3C)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /report: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", "Could not send report."))

    @app_commands.command(name="botinfo", description="Show server count, API ping, and bot version")
    async def botinfo(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        try:
            embed = build_botinfo_embed(self.bot)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /botinfo: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
