import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.player_stats import PlayerStatsParser
from core.skyblock_time import SkyblockTimeCalculator
from utils.embeds import build_fishing_stats_embed, build_fishing_events_embed, build_fishing_profit_embed, build_error_embed

logger = logging.getLogger(__name__)

class FishingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="fishing_stats", description="Show fishing level, total sea creatures killed, and trophy fishing progress")
    @app_commands.describe(player="Minecraft username or UUID")
    async def fishing_stats(self, interaction: discord.Interaction, player: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles = profiles_data.get("profiles", [])
            
            if not profiles:
                await interaction.followup.send(embed=build_error_embed("No Profile", f"{display_name} has no profiles."))
                return
                
            selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
            stats = PlayerStatsParser.get_fishing_stats(selected, uuid)
            
            embed = build_fishing_stats_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /fishing_stats: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="fishing_events", description="Show a timer for the next Spooky Festival, Jerry Pond, and Shark Scale events")
    async def fishing_events(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        try:
            events = SkyblockTimeCalculator.get_upcoming_events()
            embed = build_fishing_events_embed(events)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /fishing_events: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="fishing_profit", description="Calculate average hourly profit based on current Bazaar prices")
    @app_commands.describe(bait="The bait you are using", rod="The fishing rod you are using")
    async def fishing_profit(self, interaction: discord.Interaction, bait: str, rod: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            embed = build_fishing_profit_embed(bait, rod)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /fishing_profit: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishingCog(bot))
