import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.player_stats import PlayerStatsParser
from utils.embeds import build_mp_embed, build_missing_acc_embed, build_upgrade_cost_embed, build_error_embed

logger = logging.getLogger(__name__)

class AccessoriesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="mp", description="Show Magical Power, equipped Power Stone, and Tuning points")
    @app_commands.describe(player="Minecraft username or UUID")
    async def mp(self, interaction: discord.Interaction, player: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles = profiles_data.get("profiles", [])
            
            if not profiles:
                await interaction.followup.send(embed=build_error_embed("No Profile", f"{display_name} has no profiles."))
                return
                
            selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
            stats = PlayerStatsParser.get_magical_power(selected, uuid)
            
            embed = build_mp_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /mp: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="missing_accessories", description="List missing accessories sorted by cheapest 'Coins per MP'")
    @app_commands.describe(player="Minecraft username or UUID")
    async def missing_accessories(self, interaction: discord.Interaction, player: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            # Placeholder for Option A
            embed = build_missing_acc_embed(display_name)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /missing_accessories: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="upgrade_cost", description="Calculate coin cost to reach a specific target MP")
    @app_commands.describe(player="Minecraft username or UUID", target_mp="The magical power you want to reach")
    async def upgrade_cost(self, interaction: discord.Interaction, player: str, target_mp: int) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            embed = build_upgrade_cost_embed(display_name, target_mp)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /upgrade_cost: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AccessoriesCog(bot))
