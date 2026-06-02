"""Skyblock Bot — main entry point.

Initialises core services (API clients, caches, database, analyzers),
loads cogs, syncs slash commands, and runs the Discord event loop.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

import config
from core.analyzer import MarketAnalyzer
from core.auctions import AuctionCache
from core.bazaar import BazaarCache
from core.collections import CollectionTracker
from core.hypixel_client import HypixelClient
from core.mojang_client import MojangClient
from storage.database import Database

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("skyblock_bot")


# ── Bot ──────────────────────────────────────────────────────────────────────

class SkyblockBot(commands.Bot):
    """Custom bot subclass that wires up every core service."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        # Core services — initialised here so cogs can access them via self.bot
        self.hypixel = HypixelClient(config.HYPIXEL_API_KEY, config.HYPIXEL_BASE_URL)
        self.mojang = MojangClient(config.MOJANG_BASE_URL)
        self.db = Database(config.DB_PATH)
        self.bazaar_cache = BazaarCache(
            self.hypixel, self.db, ttl=config.BAZAAR_CACHE_TTL
        )
        self.auction_cache = AuctionCache(
            self.hypixel, self.db, ttl=config.AUCTION_CACHE_TTL
        )
        self.analyzer = MarketAnalyzer(
            self.db,
            min_margin_pct=config.MIN_PROFIT_MARGIN_PCT,
            min_profit=config.MIN_PROFIT_ABSOLUTE,
            top_count=config.TOP_FLIPS_COUNT,
        )
        self.collection_tracker = CollectionTracker(self.hypixel)

    # ── Lifecycle hooks ──────────────────────────────────────────────────────

    async def setup_hook(self) -> None:
        """Called once before the bot connects.  Sets up DB, cogs, & commands."""
        logger.info("Initializing database...")
        await self.db.initialize()

        logger.info("Loading collection definitions...")
        await self.collection_tracker.load_definitions()

        logger.info("Loading cogs...")
        await self.load_extension("cogs.market")
        await self.load_extension("cogs.player")

        # Sync slash commands to the configured guild for instant availability
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            try:
                await self.tree.sync(guild=guild)
                logger.info("Synced commands to guild %s", config.GUILD_ID)
            except discord.Forbidden:
                logger.warning(
                    "Cannot sync commands to guild %s — Missing Access. "
                    "Make sure the bot is invited with the 'applications.commands' scope. "
                    "Invite URL: https://discord.com/oauth2/authorize?"
                    "client_id=%s&permissions=83968&scope=bot%%20applications.commands",
                    config.GUILD_ID,
                    self.application_id,
                )
                # Fall back to global sync
                await self.tree.sync()
                logger.info("Fell back to global command sync (may take up to 1 hour)")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally (may take up to 1 hour)")

        # Start periodic cleanup
        self.cleanup_task.start()

    async def on_ready(self) -> None:
        """Fires when the bot has connected and is ready."""
        assert self.user is not None
        logger.info("Bot is ready! Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Connected to %d guild(s)", len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Skyblock Markets 📈",
            )
        )

    # ── Background tasks ─────────────────────────────────────────────────────

    @tasks.loop(hours=6)
    async def cleanup_task(self) -> None:
        """Periodically clean up old database records."""
        try:
            deleted = await self.db.cleanup(days=7)
            if deleted > 0:
                logger.info("Cleaned up %d old database records", deleted)
        except Exception as e:
            logger.error("Cleanup error: %s", e)

    @cleanup_task.before_loop
    async def before_cleanup(self) -> None:
        await self.wait_until_ready()

    # ── Shutdown ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Gracefully shut down all services before disconnecting."""
        logger.info("Shutting down...")
        await self.hypixel.close()
        await self.mojang.close()
        await self.db.close()
        await super().close()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    """Validate configuration and start the bot."""
    if not config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in .env file!")
        return
    if not config.HYPIXEL_API_KEY or config.HYPIXEL_API_KEY == "YOUR_HYPIXEL_API_KEY_HERE":
        logger.warning("HYPIXEL_API_KEY not set — API calls will fail!")

    bot = SkyblockBot()
    bot.run(config.DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
