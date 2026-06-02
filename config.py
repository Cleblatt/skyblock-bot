"""Configuration loader for Skyblock Bot.

Loads environment variables from .env and exposes typed configuration
constants used throughout the application.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Discord ──────────────────────────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
GUILD_ID: int = int(os.getenv('GUILD_ID', '0'))
AUTO_POST_CHANNEL_ID: str = os.getenv('AUTO_POST_CHANNEL_ID', '')

# ── Hypixel ──────────────────────────────────────────────────────────────────
HYPIXEL_API_KEY: str = os.getenv('HYPIXEL_API_KEY', '')
HYPIXEL_BASE_URL: str = 'https://api.hypixel.net/v2'
MOJANG_BASE_URL: str = 'https://api.mojang.com'

# ── Cache TTL (seconds) ─────────────────────────────────────────────────────
BAZAAR_CACHE_TTL: int = 60
AUCTION_CACHE_TTL: int = 120

# ── Market analysis ─────────────────────────────────────────────────────────
MIN_PROFIT_MARGIN_PCT: float = 10.0
MIN_PROFIT_ABSOLUTE: int = 50_000
HISTORY_WINDOW_HOURS: int = 24
TOP_FLIPS_COUNT: int = 10

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH: str = './data/skyblock.db'

# ── Auto-post interval (seconds) ────────────────────────────────────────────
AUTO_POST_INTERVAL: int = 300
