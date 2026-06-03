"""Player commands Cog — /progress and /collections.

Provides slash commands for inspecting a Skyblock player's collection
progress, including per-collection tier tracking and a full category
overview.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.mojang_client import PlayerNotFoundError
from utils.embeds import (
    build_collections_overview_embeds,
    build_error_embed,
    build_progress_embed,
)

logger = logging.getLogger(__name__)


class PlayerCog(commands.Cog):
    """Cog housing player-related slash commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /progress ────────────────────────────────────────────────────────────

    @app_commands.command(
        name="progress",
        description="Track collection progress and resources needed for a player",
    )
    @app_commands.describe(
        username="Minecraft username or UUID",
        collection="Specific collection to check (e.g. wheat, diamond). Leave blank for overview.",
        target_tier="Target tier to calculate remaining resources for",
    )
    async def progress(
        self,
        interaction: discord.Interaction,
        username: str,
        collection: str | None = None,
        target_tier: int | None = None,
    ) -> None:
        """Show how far a player is from the next (or a target) tier."""
        await interaction.response.defer(thinking=True)
        try:
            # Resolve Minecraft username → UUID
            uuid, display_name = await self.bot.mojang.resolve(username)

            # Fetch Skyblock profiles
            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles: list[dict] = profiles_data.get("profiles", [])

            if not profiles:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "No Profile",
                        f"{display_name} has no Skyblock profiles.",
                    )
                )
                return

            # Pick the currently selected profile
            selected = next(
                (p for p in profiles if p.get("selected", False)),
                profiles[0],
            )

            member_data = selected.get("members", {}).get(uuid, {})
            player_collections: dict = member_data.get("collection", {})

            if not player_collections:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "No Collections",
                        f"No collection data found for {display_name}.",
                    )
                )
                return

            # Optionally resolve a specific collection filter
            collection_filter = None
            if collection:
                collection_filter = self.bot.collection_tracker.find_collection_by_name(
                    collection
                )
                if not collection_filter:
                    await interaction.followup.send(
                        embed=build_error_embed(
                            "Unknown Collection",
                            f'Could not find a collection matching "{collection}". '
                            "Try: wheat, diamond, oak_log, etc.",
                        )
                    )
                    return

            # Calculate and send progress
            progress_list = self.bot.collection_tracker.get_progress(
                player_collections, collection_filter, target_tier
            )
            embed = build_progress_embed(display_name, progress_list, target_tier)

            cute_name = selected.get("cute_name", "Unknown")
            embed.set_author(name=f"Profile: {cute_name}")
            await interaction.followup.send(embed=embed)

        except PlayerNotFoundError:
            await interaction.followup.send(
                embed=build_error_embed(
                    "Player Not Found",
                    f'Could not find Minecraft player "{username}".',
                )
            )
        except Exception as e:
            logger.error("Error in /progress: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=build_error_embed(
                    "Error",
                    f"Failed to fetch player data: {e}",
                )
            )

    # ── /collections ─────────────────────────────────────────────────────────

    @app_commands.command(
        name="collections",
        description="View all collection tiers for a player",
    )
    @app_commands.describe(username="Minecraft username or UUID")
    async def collections(
        self,
        interaction: discord.Interaction,
        username: str,
    ) -> None:
        """Display an overview of every collection grouped by category."""
        await interaction.response.defer(thinking=True)
        try:
            uuid, display_name = await self.bot.mojang.resolve(username)

            profiles_data = await self.bot.hypixel.get_player_profiles(uuid)
            profiles: list[dict] = profiles_data.get("profiles", [])

            if not profiles:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "No Profile",
                        f"{display_name} has no Skyblock profiles.",
                    )
                )
                return

            selected = next(
                (p for p in profiles if p.get("selected", False)),
                profiles[0],
            )

            member_data = selected.get("members", {}).get(uuid, {})
            player_collections: dict = member_data.get("collection", {})

            if not player_collections:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "No Collections",
                        f"No collection data found for {display_name}.",
                    )
                )
                return

            progress_list = self.bot.collection_tracker.get_progress(player_collections)
            embeds = build_collections_overview_embeds(display_name, progress_list)

            # Discord allows up to 10 embeds per message
            for i in range(0, len(embeds), 10):
                batch = embeds[i : i + 10]
                await interaction.followup.send(embeds=batch)

        except PlayerNotFoundError:
            await interaction.followup.send(
                embed=build_error_embed(
                    "Player Not Found",
                    f'Could not find Minecraft player "{username}".',
                )
            )
        except Exception as e:
            logger.error("Error in /collections: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=build_error_embed(
                    "Error",
                    f"Failed to fetch player data: {e}",
                )
            )


async def setup(bot: commands.Bot) -> None:
    """Entry-point called by ``bot.load_extension('cogs.player')``."""
    await bot.add_cog(PlayerCog(bot))
