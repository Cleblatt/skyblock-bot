import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.player_stats import PlayerStatsParser
from utils.embeds import build_slayer_embed, build_all_slayers_embed, build_bestiary_embed, build_rng_calc_embed, build_error_embed

logger = logging.getLogger(__name__)


class HuntingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _get_selected_profile(self, player: str) -> tuple[str, str, dict]:
        """Resolve player and return (uuid, display_name, selected_profile)."""
        uuid, display_name = await self.bot.mojang.resolve(player)
        profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
        profiles = profiles_data.get("profiles", [])
        if not profiles:
            raise ValueError(f"{display_name} has no Skyblock profiles.")
        selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
        return uuid, display_name, selected

    @app_commands.command(name="slayer", description="Show levels, XP, and kills for a specific slayer boss (or all)")
    @app_commands.describe(player="Minecraft username or UUID", boss="The slayer boss (zombie, spider, wolf, enderman, blaze, vampire). Leave empty for all.")
    async def slayer(self, interaction: discord.Interaction, player: str, boss: str | None = None) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await self._get_selected_profile(player)

            if boss:
                stats = PlayerStatsParser.get_slayer_stats(selected, uuid, boss)
                if not stats:
                    await interaction.followup.send(embed=build_error_embed("Not Found", f"No slayer data found for '{boss}'."))
                    return
                embed = build_slayer_embed(display_name, stats)
            else:
                all_slayers = PlayerStatsParser.get_all_slayers(selected, uuid)
                embed = build_all_slayers_embed(display_name, all_slayers)

            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("No Profile", str(e)))
        except Exception as e:
            logger.error("Error in /slayer: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="bestiary", description="Recommend the easiest bestiary milestones to complete next")
    @app_commands.describe(player="Minecraft username or UUID")
    async def bestiary(self, interaction: discord.Interaction, player: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await self._get_selected_profile(player)
            stats = PlayerStatsParser.get_bestiary_stats(selected, uuid)
            embed = build_bestiary_embed(display_name, stats)
            await interaction.followup.send(embed=embed)
        except PlayerNotFoundError:
            await interaction.followup.send(embed=build_error_embed("Player Not Found", f"Could not find {player}."))
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("No Profile", str(e)))
        except Exception as e:
            logger.error("Error in /bestiary: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    @app_commands.command(name="rng_calc", description="Calculate drop chances for RNG items based on your Magic Find")
    @app_commands.describe(item="The RNG drop item (e.g. warden heart, necrons handle)", magic_find="Your total Magic Find stat")
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
