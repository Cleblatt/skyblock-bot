import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.player_stats import PlayerStatsParser
from core.skyblock_time import SkyblockTimeCalculator
from utils.helpers import get_profile
from utils.embeds import (
    build_networth_embed, build_skills_embed, build_dungeons_embed,
    build_skyblock_time_embed, build_error_embed,
)

logger = logging.getLogger(__name__)


class UtilitiesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="networth", description="Show purse and bank balance for a player")
    @app_commands.describe(player="Minecraft username or UUID", profile="Optional: Profile name (e.g. Apple)")
    async def networth(self, interaction: discord.Interaction, player: str, profile: str | None = None) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await get_profile(self.bot, player, profile)
            stats = PlayerStatsParser.calculate_networth(selected, uuid)
            embed = build_networth_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("No Profile", str(e)))
        except Exception as e:
            logger.error("Error in /networth: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="skills", description="Show all skill levels and Skill Average for a player")
    @app_commands.describe(player="Minecraft username or UUID", profile="Optional: Profile name (e.g. Apple)")
    async def skills(self, interaction: discord.Interaction, player: str, profile: str | None = None) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await get_profile(self.bot, player, profile)
            data = PlayerStatsParser.get_skills(selected, uuid)
            embed = build_skills_embed(display_name, data)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("No Profile", str(e)))
        except Exception as e:
            logger.error("Error in /skills: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="dungeons", description="Show Catacombs level, Class levels, and floor completions")
    @app_commands.describe(player="Minecraft username or UUID", profile="Optional: Profile name (e.g. Apple)")
    async def dungeons(self, interaction: discord.Interaction, player: str, profile: str | None = None) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await get_profile(self.bot, player, profile)
            stats = PlayerStatsParser.get_dungeons_stats(selected, uuid)
            embed = build_dungeons_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("No Profile", str(e)))
        except Exception as e:
            logger.error("Error in /dungeons: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="skyblock_time", description="Show current in-game Skyblock time, season, and year")
    async def skyblock_time(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        try:
            time_data = SkyblockTimeCalculator.get_current_time()
            embed = build_skyblock_time_embed(time_data)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /skyblock_time: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UtilitiesCog(bot))
