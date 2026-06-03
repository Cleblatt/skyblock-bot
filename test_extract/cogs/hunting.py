import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.player_stats import PlayerStatsParser
from utils.embeds import build_slayer_embed, build_bestiary_embed, build_rng_calc_embed, build_error_embed

logger = logging.getLogger(__name__)

class HuntingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="slayer", description="Show levels, XP, and kills for a specific slayer boss")
    @app_commands.describe(player="Minecraft username or UUID", boss="The slayer boss (e.g. zombie, spider, wolf, enderman, blaze, vampire)")
    async def slayer(self, interaction: discord.Interaction, player: str, boss: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles = profiles_data.get("profiles", [])
            
            if not profiles:
                await interaction.followup.send(embed=build_error_embed("No Profile", f"{display_name} has no profiles."))
                return
                
            selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
            stats = PlayerStatsParser.get_slayer_stats(selected, uuid, boss)
            
            if not stats:
                await interaction.followup.send(embed=build_error_embed("Not Found", f"No slayer data found for '{boss}' on this profile."))
                return
                
            embed = build_slayer_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /slayer: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="bestiary", description="Recommend the easiest bestiary milestones to complete next")
    @app_commands.describe(player="Minecraft username or UUID")
    async def bestiary(self, interaction: discord.Interaction, player: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(player)
            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles = profiles_data.get("profiles", [])
            
            if not profiles:
                await interaction.followup.send(embed=build_error_embed("No Profile", f"{display_name} has no profiles."))
                return
                
            selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
            stats = PlayerStatsParser.get_bestiary_stats(selected, uuid)
            
            embed = build_bestiary_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except Exception as e:
            logger.error("Error in /bestiary: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="rng_calc", description="Calculate exact percentage drop chances for RNG items")
    @app_commands.describe(item="The RNG drop item", magic_find="Your total Magic Find")
    async def rng_calc(self, interaction: discord.Interaction, item: str, magic_find: int) -> None:
        await interaction.response.defer(thinking=True)
        try:
            embed = build_rng_calc_embed(item, magic_find)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /rng_calc: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HuntingCog(bot))
