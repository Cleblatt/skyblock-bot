"""Discord embed builders for the Skyblock Bot.

Provides richly-formatted embed constructors for market flips, bazaar
details, collection progress, and error states.
"""

from __future__ import annotations

from typing import Any

import discord


# ── Formatting helpers ───────────────────────────────────────────────────────

def format_coins(n: int | float) -> str:
    """Format a coin value for display.

    * Under 1 M → comma-separated (e.g. ``1,234,567``)
    * 1 M – 999.9 M → ``1.2M``
    * 1 B+ → ``1.2B``
    """
    if n is None:
        return "N/A"
    n = float(n)
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1_000_000_000:
        return f"{sign}{abs_n / 1_000_000_000:,.1f}B"
    if abs_n >= 1_000_000:
        return f"{sign}{abs_n / 1_000_000:,.1f}M"
    return f"{sign}{abs_n:,.0f}"


def progress_bar(pct: float, length: int = 10) -> str:
    """Build a Unicode progress bar.

    ``75%`` with *length* 10 → ``'████████░░'``
    """
    pct = max(0.0, min(100.0, pct))
    filled = round(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)


# ── Category helpers ─────────────────────────────────────────────────────────

_CATEGORY_EMOJIS: dict[str, str] = {
    "farming": "🌾",
    "mining": "⛏️",
    "combat": "⚔️",
    "foraging": "🌲",
    "fishing": "🎣",
}

_CATEGORY_COLORS: dict[str, int] = {
    "farming": 0x2ECC71,
    "mining": 0x95A5A6,
    "combat": 0xE74C3C,
    "foraging": 0x27AE60,
    "fishing": 0x3498DB,
}


def _get_category_emoji(category: str) -> str:
    """Return an emoji for the given collection category."""
    return _CATEGORY_EMOJIS.get(category.lower(), "📦")


def _get_category_color(category: str) -> int:
    """Return the embed colour for a collection category."""
    return _CATEGORY_COLORS.get(category.lower(), 0x00CED1)


# ── Embed builders ───────────────────────────────────────────────────────────

def build_flips_embed(flips: list[Any]) -> discord.Embed:
    """Build an embed showcasing the top flipping opportunities.

    Parameters
    ----------
    flips:
        A list of flip data-objects.  Each must expose ``confidence``,
        ``item_name``, ``source``, ``buy_price``, ``sell_price``,
        ``profit``, ``margin_pct``, and ``volume`` attributes.
    """
    if not flips:
        embed = discord.Embed(
            title="💰 Top Skyblock Flipping Opportunities",
            description=(
                "No profitable flips found at the moment. "
                "The market might be stable — check back later!"
            ),
            color=0xFFD700,
        )
        embed.set_footer(text="Last updated")
        embed.timestamp = discord.utils.utcnow()
        embed.set_thumbnail(
            url="https://mc-heads.net/head/notch"
        )
        return embed

    embed = discord.Embed(
        title="💰 Top Skyblock Flipping Opportunities",
        description=f"Found **{len(flips)}** profitable flips. Here are the best deals:",
        color=0xFFD700,
    )

    for flip in flips[:10]:
        confidence_emoji = flip.confidence.split()[0] if flip.confidence else "❓"
        embed.add_field(
            name=f"{confidence_emoji} {flip.item_name}",
            value=(
                f"**Source:** {flip.source}\n"
                f"**Buy:** {format_coins(flip.buy_price)}\n"
                f"**Sell:** {format_coins(flip.sell_price)}\n"
                f"**Profit:** +{format_coins(flip.profit)} ({flip.margin_pct:.1f}%)\n"
                f"**Volume:** {format_coins(flip.volume)}/week"
            ),
            inline=True,
        )

    embed.set_footer(text="Last updated")
    embed.timestamp = discord.utils.utcnow()
    embed.set_thumbnail(
        url="https://mc-heads.net/head/notch"
    )
    return embed


def build_bazaar_detail_embed(
    product: Any,
    hist_avg: tuple[float, float] | None = None,
) -> discord.Embed:
    """Build a detailed Bazaar product embed.

    Parameters
    ----------
    product:
        A ``BazaarProduct`` exposing ``product_id``, ``buy_price``,
        ``sell_price``, ``spread``, ``spread_pct``, ``buy_volume``,
        ``sell_volume``, and ``moving_week``.
    hist_avg:
        A ``(avg_buy, avg_sell)`` tuple from the database, or ``None``
        if no historical data is available yet.
    """
    title = product.product_id.replace("_", " ").title()
    embed = discord.Embed(
        title=f"📊 Bazaar — {title}",
        color=0x00CED1,
    )
    embed.add_field(name="Buy Price (instant sell)", value=format_coins(product.buy_price), inline=True)
    embed.add_field(name="Sell Price (instant buy)", value=format_coins(product.sell_price), inline=True)
    embed.add_field(
        name="Spread",
        value=f"{format_coins(product.spread)} ({product.spread_pct:.1f}%)",
        inline=True,
    )
    embed.add_field(name="Buy Volume", value=format_coins(product.buy_volume), inline=True)
    embed.add_field(name="Sell Volume", value=format_coins(product.sell_volume), inline=True)
    embed.add_field(name="Weekly Volume", value=format_coins(product.moving_week), inline=True)

    if hist_avg:
        embed.add_field(name="24h Avg Buy", value=format_coins(hist_avg[0]), inline=True)
        embed.add_field(name="24h Avg Sell", value=format_coins(hist_avg[1]), inline=True)

    embed.set_footer(text="Last updated")
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_progress_embed(
    username: str,
    progress_list: list[Any],
    target_tier: int | None = None,
) -> discord.Embed:
    """Build a collection-progress embed for a single player.

    Parameters
    ----------
    username:
        The player display name.
    progress_list:
        ``CollectionProgress`` objects exposing ``category``, ``name``,
        ``current_tier``, ``max_tier``, ``next_tier``, ``progress_pct``,
        ``current_amount``, ``next_tier_req``, and ``remaining``.
    target_tier:
        Optional target tier the user asked about.
    """
    embed = discord.Embed(
        title=f"📊 Collection Progress — {username}",
        color=0x00CED1,
    )

    if not progress_list:
        embed.description = "No collection data found for this player."
        return embed

    for entry in progress_list[:15]:
        emoji = _get_category_emoji(entry.category)
        bar = progress_bar(entry.progress_pct)
        tier_display = f"Tier {entry.current_tier}/{entry.max_tier}"
        embed.add_field(
            name=f"{emoji} {entry.name}",
            value=(
                f"**{tier_display}** → Tier {entry.next_tier}\n"
                f"{bar} {entry.progress_pct:.1f}%\n"
                f"Collected: {format_coins(entry.current_amount)} / {format_coins(entry.next_tier_req)}\n"
                f"**Remaining: {format_coins(entry.remaining)}**"
            ),
            inline=False,
        )

    embed.set_footer(text=f"Player: {username}")
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_collections_overview_embeds(
    username: str,
    progress_list: list[Any],
) -> list[discord.Embed]:
    """Group collections by category and return one embed per category.

    Parameters
    ----------
    username:
        The player display name.
    progress_list:
        ``CollectionProgress`` objects (same shape as
        :func:`build_progress_embed`).
    """
    grouped: dict[str, list[Any]] = {}
    for entry in progress_list:
        grouped.setdefault(entry.category.lower(), []).append(entry)

    embeds: list[discord.Embed] = []
    for category, items in grouped.items():
        emoji = _get_category_emoji(category)
        color = _get_category_color(category)
        embed = discord.Embed(
            title=f"{emoji} {category.title()} Collections — {username}",
            color=color,
        )
        for col in items:
            embed.add_field(
                name=col.name,
                value=f"Tier {col.current_tier}/{col.max_tier} | {format_coins(col.current_amount)}",
                inline=True,
            )
        embed.set_footer(text="Last updated")
        embed.timestamp = discord.utils.utcnow()
        embeds.append(embed)

    if not embeds:
        embeds.append(
            discord.Embed(
                title=f"📊 Collections — {username}",
                description="No collection data found for this player.",
                color=0x00CED1,
            )
        )

    return embeds


def build_error_embed(title: str, description: str) -> discord.Embed:
    """Build a simple red error embed."""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xE74C3C,
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


# ── New Command Embeds (Option A) ────────────────────────────────────────────

def build_mp_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🪄 Magical Power — {username}", color=0x9B59B6)
    embed.add_field(name="Total MP", value=f"**{stats['mp']}**", inline=True)
    embed.add_field(name="Selected Power", value=stats['power'], inline=True)
    embed.add_field(name="Tuning Points", value=str(stats['tuning_points']), inline=True)
    return embed

def build_missing_acc_embed(username: str) -> discord.Embed:
    embed = discord.Embed(title=f"🔍 Missing Accessories — {username}", color=0xE67E22)
    embed.description = (
        "*(Placeholder for Option A)*\n\n"
        "1. **Ender Relic** - 50m coins (1,000,000 / MP)\n"
        "2. **Hegemony Artifact** - 400m coins (2,000,000 / MP)\n"
        "3. **Wither Relic** - 15m coins (3,000,000 / MP)"
    )
    return embed

def build_upgrade_cost_embed(username: str, target: int) -> discord.Embed:
    embed = discord.Embed(title=f"💰 Upgrade Cost — {username}", color=0xF1C40F)
    embed.description = f"To reach **{target} MP**, you need approx **250,000,000 Coins**. *(Placeholder)*"
    return embed

def build_fishing_stats_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🎣 Fishing Stats — {username}", color=0x3498DB)
    embed.add_field(name="Fishing Level", value=f"Level {stats['level']}", inline=True)
    embed.add_field(name="Sea Creatures Killed", value=format_coins(stats['sc_kills']), inline=True)
    embed.add_field(name="Trophy Fish Caught", value=format_coins(stats['trophy_fish_caught']), inline=True)
    return embed

def build_fishing_events_embed(events: list) -> discord.Embed:
    embed = discord.Embed(title="📅 Upcoming Skyblock Events", color=0x1ABC9C)
    for e in events:
        mins = e.starts_in_seconds // 60
        embed.add_field(name=e.name, value=f"{e.description}\n**Starts in:** {mins} minutes", inline=False)
    return embed

def build_fishing_profit_embed(bait: str, rod: str) -> discord.Embed:
    embed = discord.Embed(title="🦈 Fishing Profit Calculator", color=0x2ECC71)
    embed.description = f"Using **{bait.title()}** and **{rod.title()}**:\n\nEstimated Profit: **2,500,000 Coins / hour** *(Placeholder)*"
    return embed

def build_slayer_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"⚔️ Slayer — {username}", color=0xE74C3C)
    embed.add_field(name="Boss", value=stats['boss'], inline=True)
    embed.add_field(name="Level", value=f"Level {stats['level']}", inline=True)
    embed.add_field(name="Total XP", value=format_coins(stats['xp']), inline=True)
    embed.add_field(name="Total Kills", value=format_coins(stats['kills']), inline=True)
    return embed

def build_bestiary_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🦇 Bestiary — {username}", color=0x8E44AD)
    embed.description = f"**Current Milestone:** {stats['milestone']}\n\n**Easiest Next Targets:**\n"
    for r in stats['recommendations']:
        embed.description += f"• {r}\n"
    return embed

def build_rng_calc_embed(item: str, magic_find: int) -> discord.Embed:
    embed = discord.Embed(title="🎲 RNG Drop Calculator", color=0xD35400)
    mf_mult = 1 + (magic_find / 100)
    embed.description = f"Item: **{item.title()}**\nMagic Find: **{magic_find}**\n\nDrop Chance: **{0.05 * mf_mult:.4f}%** *(Placeholder)*"
    return embed

def build_craft_profit_embed(craft: Any) -> discord.Embed:
    embed = discord.Embed(title=f"⚒️ Craft Profit — {craft.item_name}", color=0x2ECC71)
    embed.add_field(name="Recipe", value=craft.recipe_str, inline=False)
    embed.add_field(name="Crafting Cost", value=format_coins(craft.craft_cost), inline=True)
    embed.add_field(name="Sell Price (AH/Bz)", value=format_coins(craft.sell_price), inline=True)
    embed.add_field(name="Expected Profit", value=f"+{format_coins(craft.profit)} ({craft.margin_pct:.1f}%)", inline=False)
    return embed

def build_price_embed(item: str, price: float) -> discord.Embed:
    embed = discord.Embed(title=f"🏷️ Market Value — {item.title()}", color=0xF39C12)
    embed.description = f"Current Lowest Price: **{format_coins(price)}**"
    return embed

def build_networth_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"💰 Networth — {username}", color=0xF1C40F)
    embed.add_field(name="Total Networth", value=f"**{format_coins(stats['total'])}**", inline=False)
    embed.add_field(name="Purse", value=format_coins(stats['purse']), inline=True)
    embed.add_field(name="Bank", value=format_coins(stats['bank']), inline=True)
    embed.add_field(name="Items & Storage", value=f"{format_coins(stats['items'])} *(Estimate)*", inline=True)
    return embed

def build_skills_embed(username: str, sa: float) -> discord.Embed:
    embed = discord.Embed(title=f"📊 Skill Average — {username}", color=0x27AE60)
    embed.description = f"True Skill Average: **{sa}**"
    return embed

def build_dungeons_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"💀 Dungeons — {username}", color=0x34495E)
    embed.add_field(name="Catacombs Level", value=f"Level {stats['catacombs_level']}", inline=False)
    embed.add_field(name="Total Completions", value=format_coins(stats['total_completions']), inline=False)
    for c, l in stats['classes'].items():
        embed.add_field(name=c, value=f"Level {l}", inline=True)
    return embed

def build_skyblock_time_embed(time_data: dict) -> discord.Embed:
    embed = discord.Embed(title="⏰ Skyblock Time", color=0x2980B9)
    embed.add_field(name="Time", value=time_data['time'], inline=True)
    embed.add_field(name="Day", value=f"Day {time_data['day']}", inline=True)
    embed.add_field(name="Season", value=time_data['month_name'], inline=True)
    embed.add_field(name="Year", value=f"Year {time_data['year']}", inline=True)
    return embed

def build_botinfo_embed(bot: Any) -> discord.Embed:
    embed = discord.Embed(title="🤖 Bot Info", color=0x7F8C8D)
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Version", value="2.0.0", inline=True)
    return embed
