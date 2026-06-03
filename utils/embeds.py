"""Discord embed builders for the Skyblock Bot.

Provides richly-formatted embed constructors for market flips, bazaar
details, collection progress, player stats, and error states.
"""

from __future__ import annotations

from typing import Any

import discord


# ── Formatting helpers ───────────────────────────────────────────────────────

def format_coins(n: int | float) -> str:
    """Format a coin value for display."""
    if n is None:
        return "0"
    n = float(n)
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n:,.0f}"


def progress_bar(pct: float, length: int = 10) -> str:
    """Unicode progress bar."""
    filled = int(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)


def _get_category_emoji(category: str) -> str:
    """Return emoji for collection category."""
    emojis = {
        "farming": "🌾", "mining": "⛏️", "combat": "⚔️",
        "foraging": "🌲", "fishing": "🎣", "boss": "💀",
    }
    return emojis.get(category.lower(), "📦")


# ── Market Embeds ────────────────────────────────────────────────────────────

def build_flips_embed(flips: list) -> discord.Embed:
    """Build embed for /flips command."""
    embed = discord.Embed(
        title="💰 Top Skyblock Flipping Opportunities",
        color=0xFFD700,
    )
    if not flips:
        embed.description = "No profitable flips found at the moment. The market might be stable — check back later!"
    else:
        embed.description = f"Found **{len(flips)}** profitable flips:"
        for flip in flips[:10]:
            emoji = flip.confidence.split()[0] if flip.confidence else "⚪"
            embed.add_field(
                name=f"{emoji} {flip.item_name}",
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
    return embed


def build_bazaar_detail_embed(product: Any, hist_avg: tuple) -> discord.Embed:
    """Build detailed Bazaar embed for /bazaar command."""
    embed = discord.Embed(
        title=f"📊 Bazaar — {product.product_id.replace('_', ' ').title()}",
        color=0x00CED1,
    )
    embed.add_field(name="Buy Price (Instant Sell)", value=format_coins(product.buy_price), inline=True)
    embed.add_field(name="Sell Price (Instant Buy)", value=format_coins(product.sell_price), inline=True)
    embed.add_field(name="Spread", value=f"{format_coins(product.spread)} ({product.spread_pct:.1f}%)", inline=True)
    embed.add_field(name="Buy Volume", value=format_coins(product.buy_volume), inline=True)
    embed.add_field(name="Sell Volume", value=format_coins(product.sell_volume), inline=True)
    embed.add_field(name="Weekly Volume", value=format_coins(product.moving_week), inline=True)
    if hist_avg and hist_avg[0]:
        embed.add_field(name="24h Avg Buy", value=format_coins(hist_avg[0]), inline=True)
        embed.add_field(name="24h Avg Sell", value=format_coins(hist_avg[1]), inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_progress_embed(username: str, progress_list: list, target_tier: int = None) -> discord.Embed:
    """Build embed for /progress command."""
    embed = discord.Embed(
        title=f"📊 Collection Progress — {username}",
        color=0x00CED1,
    )
    if not progress_list:
        embed.description = "No collection data found for this player."
        return embed
    for p in progress_list[:15]:
        bar = progress_bar(p.progress_pct)
        tier_display = f"Tier {p.current_tier}/{p.max_tier}"
        embed.add_field(
            name=f"{_get_category_emoji(p.category)} {p.name}",
            value=(
                f"**{tier_display}** → Tier {p.next_tier}\n"
                f"{bar} {p.progress_pct:.1f}%\n"
                f"Collected: {format_coins(p.current_amount)} / {format_coins(p.next_tier_req)}\n"
                f"**Remaining: {format_coins(p.remaining)}**"
            ),
            inline=False,
        )
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_collections_overview_embeds(username: str, progress_list: list) -> list[discord.Embed]:
    """Build one embed per category for /collections."""
    category_colors = {
        "farming": 0x2ECC71, "mining": 0x95A5A6, "combat": 0xE74C3C,
        "foraging": 0x27AE60, "fishing": 0x3498DB, "boss": 0x8E44AD,
    }
    categories: dict[str, list] = {}
    for p in progress_list:
        categories.setdefault(p.category, []).append(p)

    embeds = []
    for cat, items in categories.items():
        emoji = _get_category_emoji(cat)
        color = category_colors.get(cat, 0x95A5A6)
        embed = discord.Embed(title=f"{emoji} {cat.title()} Collections — {username}", color=color)
        for c in items[:25]:
            embed.add_field(name=c.name, value=f"Tier {c.current_tier}/{c.max_tier} | {format_coins(c.current_amount)}", inline=True)
        embeds.append(embed)
    return embeds


def build_error_embed(title: str, description: str) -> discord.Embed:
    """Build a simple red error embed."""
    embed = discord.Embed(title=f"❌ {title}", description=description, color=0xE74C3C)
    embed.timestamp = discord.utils.utcnow()
    return embed


# ── Player Stats Embeds ──────────────────────────────────────────────────────

def build_mp_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🪄 Magical Power — {username}", color=0x9B59B6)
    embed.add_field(name="Total MP", value=f"**{stats['mp']:,}**", inline=True)
    embed.add_field(name="Selected Power", value=stats['power'], inline=True)
    embed.add_field(name="Tuning Points", value=str(stats['tuning_points']), inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_accessories_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"💎 Accessories — {username}", color=0x9B59B6)
    embed.add_field(name="Magical Power", value=f"**{stats['mp']:,}**", inline=True)
    embed.add_field(name="Selected Power", value=stats['power'], inline=True)
    embed.add_field(name="Bag Upgrades", value=str(stats['bag_upgrades']), inline=True)
    if stats.get('tuning'):
        tuning_str = "\n".join(f"**{k}:** +{v}" for k, v in stats['tuning'].items())
        embed.add_field(name="Tuning", value=tuning_str, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_missing_acc_embed(username: str) -> discord.Embed:
    embed = discord.Embed(title=f"🔍 Missing Accessories — {username}", color=0xE67E22)
    embed.description = (
        "*(Full accessory tracking requires NBT parsing — showing common recommendations)*\n\n"
        "1. **Ender Relic** — ~50M coins\n"
        "2. **Hegemony Artifact** — ~400M coins\n"
        "3. **Wither Relic** — ~15M coins\n"
        "4. **Handy Blood Chalice** — ~1M coins\n"
        "5. **Scarf's Studies** — ~500K coins"
    )
    embed.set_footer(text="Use /mp to check your current Magical Power")
    return embed


def build_upgrade_cost_embed(username: str, target: int) -> discord.Embed:
    embed = discord.Embed(title=f"💰 Upgrade Cost — {username}", color=0xF1C40F)
    embed.description = (
        f"To reach **{target:,} MP**, estimated cost depends on your current accessories.\n"
        f"Use `/mp` to check your current MP, then compare with accessory prices on the AH."
    )
    return embed


def build_fishing_stats_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🎣 Fishing Stats — {username}", color=0x3498DB)
    embed.add_field(name="Fishing Level", value=f"**Level {stats['level']}**", inline=True)
    embed.add_field(name="Sea Creatures Killed", value=f"**{stats['sc_kills']:,}**", inline=True)
    embed.add_field(name="Trophy Fish Caught", value=f"**{stats['trophy_fish_caught']:,}**", inline=True)
    embed.add_field(name="Fishing XP", value=format_coins(stats['xp']), inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_fishing_events_embed(events: list) -> discord.Embed:
    embed = discord.Embed(title="📅 Upcoming Skyblock Events", color=0x1ABC9C)
    for e in events:
        total_secs = e.starts_in_seconds
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        if hours > 0:
            time_str = f"{hours}h {mins}m"
        else:
            time_str = f"{mins}m"
        embed.add_field(name=e.name, value=f"{e.description}\n⏱️ **Starts in:** {time_str}", inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_fishing_profit_embed(bait: str, rod: str) -> discord.Embed:
    embed = discord.Embed(title="🦈 Fishing Profit Calculator", color=0x2ECC71)
    embed.description = (
        f"**Rod:** {rod.title()}\n"
        f"**Bait:** {bait.title()}\n\n"
        f"*Profit estimation requires real-time Bazaar prices for drops. "
        f"Use `/bazaar` to check individual fish/drop prices.*"
    )
    return embed


def build_slayer_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"⚔️ Slayer — {username}", color=0xE74C3C)
    embed.add_field(name="Boss", value=f"**{stats['boss']}**", inline=True)
    embed.add_field(name="Level", value=f"**Level {stats['level']}**", inline=True)
    embed.add_field(name="Total XP", value=f"**{stats['xp']:,}**", inline=True)
    embed.add_field(name="Total Kills", value=f"**{stats['kills']:,}**", inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_all_slayers_embed(username: str, slayers: list[dict]) -> discord.Embed:
    embed = discord.Embed(title=f"⚔️ All Slayers — {username}", color=0xE74C3C)
    if not slayers:
        embed.description = "No slayer data found."
        return embed
    for s in slayers:
        embed.add_field(
            name=f"{s['boss']}",
            value=f"Level **{s['level']}** | XP: {s['xp']:,} | Kills: {s['kills']:,}",
            inline=False,
        )
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_bestiary_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🦇 Bestiary — {username}", color=0x8E44AD)
    embed.add_field(name="Unique Mobs", value=f"**{stats['total_mobs']}**", inline=True)
    embed.add_field(name="Total Kills", value=f"**{stats['total_kills']:,}**", inline=True)
    embed.add_field(name="Milestone Level", value=f"**{stats['milestone']}**", inline=True)
    if stats.get("recommendations"):
        recs = "\n".join(f"• {r}" for r in stats["recommendations"][:5])
        embed.add_field(name="Easiest Next Milestones", value=recs, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_rng_calc_embed(item: str, magic_find: int) -> discord.Embed:
    embed = discord.Embed(title="🎲 RNG Drop Calculator", color=0xD35400)
    mf_mult = 1 + (magic_find / 100)
    # Common RNG drop base rates
    base_rates = {
        "scylla": 0.0003, "giant's sword": 0.0002, "necron's handle": 0.0001,
        "warden heart": 0.01, "judgement core": 0.0003, "overflux capacitor": 0.002,
        "red claw egg": 0.005, "couture rune": 0.01, "grizzly bait": 0.008,
    }
    base = None
    for key, rate in base_rates.items():
        if item.lower() in key:
            base = rate
            break
    if base is None:
        base = 0.001  # default
    effective = base * mf_mult
    avg_kills = int(1 / effective) if effective > 0 else 999999
    embed.description = (
        f"**Item:** {item.title()}\n"
        f"**Magic Find:** +{magic_find}\n\n"
        f"**Base Drop Rate:** {base * 100:.4f}%\n"
        f"**With Magic Find:** {effective * 100:.4f}%\n"
        f"**Average Kills Needed:** ~{avg_kills:,}"
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_craft_profit_embed(craft: Any) -> discord.Embed:
    embed = discord.Embed(title=f"⚒️ Craft Profit — {craft.item_name}", color=0x2ECC71)
    embed.add_field(name="Recipe", value=craft.recipe_str, inline=False)
    embed.add_field(name="Crafting Cost", value=format_coins(craft.craft_cost), inline=True)
    embed.add_field(name="Sell Price (AH/Bz)", value=format_coins(craft.sell_price), inline=True)
    profit_str = f"+{format_coins(craft.profit)}" if craft.profit >= 0 else format_coins(craft.profit)
    embed.add_field(name="Expected Profit", value=f"{profit_str} ({craft.margin_pct:.1f}%)", inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_price_embed(item: str, price: float) -> discord.Embed:
    embed = discord.Embed(title=f"🏷️ Market Value — {item.replace('_', ' ').title()}", color=0xF39C12)
    embed.description = f"Current Lowest Price: **{format_coins(price)}**"
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_networth_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"💰 Networth — {username}", color=0xF1C40F)
    total = stats['purse'] + stats['bank']
    embed.add_field(name="Purse", value=f"**{format_coins(stats['purse'])}**", inline=True)
    embed.add_field(name="Bank", value=f"**{format_coins(stats['bank'])}**", inline=True)
    embed.add_field(name="Liquid Total", value=f"**{format_coins(total)}**", inline=True)
    if stats.get("is_estimate"):
        embed.set_footer(text="⚠️ Item networth requires NBT parsing (not included). Showing liquid coins only.")
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_skills_embed(username: str, data: dict | float) -> discord.Embed:
    embed = discord.Embed(title=f"📊 Skills — {username}", color=0x27AE60)
    if isinstance(data, dict):
        sa = data.get("skill_average", 0)
        embed.description = f"**Skill Average: {sa}**\n"
        skills = data.get("skills", {})
        for name, info in skills.items():
            bar = progress_bar(min(info['level'] / 50 * 100, 100))
            embed.add_field(name=name, value=f"Level **{info['level']}**\n{bar}", inline=True)
    else:
        embed.description = f"**Skill Average: {data}**"
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_dungeons_embed(username: str, stats: dict) -> discord.Embed:
    embed = discord.Embed(title=f"💀 Dungeons — {username}", color=0x34495E)
    embed.add_field(name="Catacombs Level", value=f"**Level {stats['catacombs_level']}**", inline=True)
    embed.add_field(name="Selected Class", value=f"**{stats.get('selected_class', 'None')}**", inline=True)
    embed.add_field(name="Total Completions", value=f"**{stats['total_completions']:,}**", inline=True)
    if stats.get("master_completions", 0) > 0:
        embed.add_field(name="Master Mode", value=f"**{stats['master_completions']:,}**", inline=True)
    for c, l in stats.get("classes", {}).items():
        embed.add_field(name=c, value=f"Level **{l}**", inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_skyblock_time_embed(time_data: dict) -> discord.Embed:
    embed = discord.Embed(title="⏰ Skyblock Time", color=0x2980B9)
    embed.add_field(name="Time", value=f"**{time_data['time']}**", inline=True)
    embed.add_field(name="Day", value=f"**Day {time_data['day']}**", inline=True)
    embed.add_field(name="Season", value=f"**{time_data['month_name']}**", inline=True)
    embed.add_field(name="Year", value=f"**Year {time_data['year']}**", inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_botinfo_embed(bot: Any) -> discord.Embed:
    embed = discord.Embed(title="🤖 Bot Info", color=0x7F8C8D)
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Version", value="2.0.0", inline=True)
    embed.timestamp = discord.utils.utcnow()
    return embed
