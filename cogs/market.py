"""Market commands Cog — /flips, /bazaar, /bins and auto-posting.

Provides slash commands for looking up Bazaar products, finding the
cheapest BIN auctions, and discovering profitable flipping opportunities.
When ``AUTO_POST_CHANNEL_ID`` is configured the cog also periodically
posts the top flips to the designated channel.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from utils.embeds import (
    build_bazaar_detail_embed,
    build_error_embed,
    build_flips_embed,
    format_coins,
)

logger = logging.getLogger(__name__)


class MarketCog(commands.Cog):
    """Cog housing all market-related slash commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Start the auto-post loop if a channel is configured
        if config.AUTO_POST_CHANNEL_ID:
            self.auto_post_flips.start()

    def cog_unload(self) -> None:
        if self.auto_post_flips.is_running():
            self.auto_post_flips.cancel()

    # ── /flips ───────────────────────────────────────────────────────────────

    @app_commands.command(
        name="flips",
        description="Find the best current flipping opportunities in Bazaar & Auctions",
    )
    async def flips(self, interaction: discord.Interaction) -> None:
        """Display the top profitable flips from both Bazaar and Auctions."""
        await interaction.response.defer(thinking=True)
        try:
            bazaar_data = await self.bot.bazaar_cache.get()
            auction_bins = await self.bot.auction_cache.get()
            flips = await self.bot.analyzer.find_all_flips(bazaar_data, auction_bins)
            embed = build_flips_embed(flips)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /flips: %s", e, exc_info=True)
            embed = build_error_embed("Error", f"Failed to fetch market data: {e}")
            await interaction.followup.send(embed=embed)

    # ── /bazaar ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="bazaar",
        description="Look up detailed Bazaar prices for a specific item",
    )
    @app_commands.describe(item="The Bazaar product name (e.g. enchanted diamond)")
    async def bazaar(self, interaction: discord.Interaction, item: str) -> None:
        """Show in-depth Bazaar pricing for a product with historical averages."""
        await interaction.response.defer(thinking=True)
        try:
            bazaar_data = await self.bot.bazaar_cache.get()

            # Attempt an exact match first, then fall back to partial
            item_upper = item.upper().replace(" ", "_")
            product = bazaar_data.get(item_upper)

            if product is None:
                for pid, p in bazaar_data.items():
                    if item_upper in pid:
                        product = p
                        break

            if not product:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "Not Found",
                        f'Could not find Bazaar product matching "{item}".',
                    )
                )
                return

            hist_avg = await self.bot.db.get_bazaar_avg(product.product_id)
            embed = build_bazaar_detail_embed(product, hist_avg)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /bazaar: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    # ── /bins ────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="bins",
        description="Look up the lowest BIN price for an Auction item",
    )
    @app_commands.describe(item="The auction item name")
    async def bins(self, interaction: discord.Interaction, item: str) -> None:
        """Find the cheapest BIN listing for an item and compare to 24 h average."""
        await interaction.response.defer(thinking=True)
        try:
            auction_bins = await self.bot.auction_cache.get()

            item_lower = item.lower()
            match_name: str | None = None
            match_price: float | None = None

            for name, price in auction_bins.items():
                if item_lower in name.lower():
                    if match_price is None or price < match_price:
                        match_name = name
                        match_price = price

            if not match_name or match_price is None:
                await interaction.followup.send(
                    embed=build_error_embed(
                        "Not Found",
                        f'No BIN auction found matching "{item}".',
                    )
                )
                return

            avg_price = await self.bot.db.get_auction_avg(match_name)

            embed = discord.Embed(
                title=f"🏷️ Lowest BIN — {match_name}",
                color=0xE67E22,
            )
            embed.add_field(
                name="Current Lowest BIN",
                value=format_coins(match_price),
                inline=True,
            )

            if avg_price and avg_price > 0:
                diff_pct = (match_price - avg_price) / avg_price * 100
                trend = "📈" if diff_pct > 0 else "📉"
                embed.add_field(
                    name="24h Average",
                    value=format_coins(avg_price),
                    inline=True,
                )
                embed.add_field(
                    name="Trend",
                    value=f"{trend} {diff_pct:+.1f}%",
                    inline=True,
                )
            else:
                embed.add_field(
                    name="24h Average",
                    value="Not enough data yet",
                    inline=True,
                )

            embed.set_footer(text="Prices update every 2 minutes")
            embed.timestamp = discord.utils.utcnow()
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error("Error in /bins: %s", e, exc_info=True)
            await interaction.followup.send(embed=build_error_embed("Error", str(e)))

    # ── Auto-post loop ───────────────────────────────────────────────────────

    @tasks.loop(seconds=config.AUTO_POST_INTERVAL)
    async def auto_post_flips(self) -> None:
        """Periodically post top flips to a designated channel."""
        try:
            channel = self.bot.get_channel(int(config.AUTO_POST_CHANNEL_ID))
            if not channel:
                return

            bazaar_data = await self.bot.bazaar_cache.get()
            auction_bins = await self.bot.auction_cache.get()
            flips = await self.bot.analyzer.find_all_flips(bazaar_data, auction_bins)

            if flips:
                embed = build_flips_embed(flips)
                await channel.send(embed=embed)
        except Exception as e:
            logger.error("Auto-post error: %s", e, exc_info=True)

    @auto_post_flips.before_loop
    async def before_auto_post(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """Entry-point called by ``bot.load_extension('cogs.market')``."""
    await bot.add_cog(MarketCog(bot))
