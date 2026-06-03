import discord
from discord import app_commands
from discord.ext import commands
import logging
from core.mojang_client import PlayerNotFoundError
from core.collections import CollectionTracker
from utils.helpers import get_profile
from utils.embeds import build_progress_embed, build_collections_overview_embeds, build_error_embed

logger = logging.getLogger(__name__)


class PlayerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.collection_tracker = CollectionTracker(bot.hypixel)
        # Assuming load_definitions was called in setup()

    @app_commands.command(
        name="progress",
        description="Show your progress toward the next tier of a specific collection"
    )
    @app_commands.describe(
        player="Minecraft username or UUID",
        collection="Name of the collection (e.g. 'Wheat', 'Diamond')",
        target_tier="Optional: Target tier to calculate remaining amount for",
        profile="Optional: Profile name (e.g. Apple)"
    )
    async def progress(
        self,
        interaction: discord.Interaction,
        player: str,
        collection: str,
        target_tier: int | None = None,
        profile: str | None = None
    ) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await get_profile(self.bot, player, profile)

            player_collections = selected.get("collection", {})
            if not player_collections:
                # Some API profiles store it in member.collection, others might not expose it
                await interaction.followup.send(
                    embed=build_error_embed("No Data", f"No collection data found for {display_name}.")
                )
                return

            # Use tracker
            progress_list = self.collection_tracker.get_progress(
                player_collections,
                collection_filter=collection,
                target_tier=target_tier
            )

            if not progress_list:
                await interaction.followup.send(
                    embed=build_error_embed("Not Found", f"Could not find a collection named '{collection}'.")
                )
                return

            embed = build_progress_embed(display_name, progress_list, target_tier)
            await interaction.followup.send(embed=embed)

        except PlayerNotFoundError:
            await interaction.followup.send(
                embed=build_error_embed("Player Not Found", f"Could not find {player}.")
            )
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))
        except Exception as e:
            logger.error("Error in /progress: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=build_error_embed("Error", "An unexpected error occurred.")
            )

    @app_commands.command(
        name="collections",
        description="Show an overview of all your collections"
    )
    @app_commands.describe(
        player="Minecraft username or UUID",
        category="Optional: Filter by category (e.g. 'farming', 'mining')",
        profile="Optional: Profile name (e.g. Apple)"
    )
    async def collections(
        self,
        interaction: discord.Interaction,
        player: str,
        category: str | None = None,
        profile: str | None = None
    ) -> None:
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name, selected = await get_profile(self.bot, player, profile)

            player_collections = selected.get("collection", {})
            if not player_collections:
                await interaction.followup.send(
                    embed=build_error_embed("No Data", f"No collection data found for {display_name}.")
                )
                return

            progress_list = self.collection_tracker.get_progress(player_collections)

            if category:
                progress_list = [p for p in progress_list if p.category == category.lower()]
                if not progress_list:
                    await interaction.followup.send(
                        embed=build_error_embed("Not Found", f"No collections found in category '{category}'.")
                    )
                    return

            embeds = build_collections_overview_embeds(display_name, progress_list)

            # Send the first embed, and others as followups if multiple
            if not embeds:
                await interaction.followup.send(
                    embed=build_error_embed("Not Found", "No collection data could be parsed.")
                )
                return

            await interaction.followup.send(embed=embeds[0])
            for embed in embeds[1:10]:  # Discord allows max 10 embeds per message if packed, but followups are safer
                await interaction.followup.send(embed=embed)

        except PlayerNotFoundError:
            await interaction.followup.send(
                embed=build_error_embed("Player Not Found", f"Could not find {player}.")
            )
        except ValueError as e:
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))
        except Exception as e:
            logger.error("Error in /collections: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=build_error_embed("Error", "An unexpected error occurred.")
            )


async def setup(bot: commands.Bot) -> None:
    cog = PlayerCog(bot)
    try:
        await cog.collection_tracker.load_definitions()
    except Exception as e:
        logger.error("Failed to load collection definitions on setup: %s", e)
    await bot.add_cog(cog)
