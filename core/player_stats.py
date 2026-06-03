"""Player Stats Parsers (v2 API).

Parses raw Hypixel API v2 profile data into readable stats for Dungeons,
Skills, Slayer, Bestiary, Fishing, and Accessories (MP).

IMPORTANT: The v2 API uses nested category objects:
- Skills: member.player_data.experience.SKILL_<NAME>
- Slayer: member.slayer.slayer_bosses.<type>
- Dungeons: member.dungeons.dungeon_types.catacombs
- Coin Purse: member.currencies.coin_purse
- Bank: profile.banking.balance (profile-level!)
- Accessory Bag: member.accessory_bag_storage
- Trophy Fish: member.trophy_fish
- Bestiary: member.bestiary
"""

import math
from typing import Any

# ── Skill XP Tables ──────────────────────────────────────────────────────────
# Standard skills cap at 50 (60 for some with skill cap increases)
SKILL_XP_TABLE = [
    0, 50, 175, 375, 675, 1175, 1925, 2925, 4425, 6425,
    9925, 14925, 22425, 32425, 47425, 67425, 97425, 147425, 222425, 322425,
    522425, 822425, 1222425, 1722425, 2322425, 3022425, 3822425, 4722425, 5722425, 6822425,
    8022425, 9322425, 10722425, 12222425, 13822425, 15522425, 17322425, 19222425, 21222425, 23322425,
    25522425, 27822425, 30222425, 32722425, 35322425, 38072425, 40972425, 44072425, 47472425, 51172425,
    55172425, 59472425, 64072425, 68972425, 74172425, 79672425, 85472425, 91572425, 97972425, 104672425,
]

# Dungeon/Catacombs XP table
DUNGEON_XP_TABLE = [
    0, 50, 125, 235, 395, 625, 955, 1425, 2095, 3045,
    4385, 6275, 8940, 12700, 17960, 25340, 35640, 50040, 70040, 97640,
    135640, 188140, 259640, 356640, 488640, 668640, 911640, 1239640, 1684640, 2284640,
    3084640, 4149640, 5559640, 7459640, 9959640, 13259640, 17559640, 23159640, 30359640, 39559640,
    51559640, 66559640, 85559640, 109559640, 139559640, 177559640, 225559640, 285559640, 360559640, 453559640,
]

SLAYER_XP_TABLE = {
    "zombie": [5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "spider": [5, 25, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "wolf":   [10, 30, 250, 1500, 5000, 20000, 100000, 400000, 1000000],
    "enderman": [10, 30, 250, 1500, 5000, 20000, 100000, 400000, 1000000],
    "blaze":  [10, 30, 250, 1500, 5000, 20000, 100000, 400000, 1000000],
    "vampire": [20, 75, 240, 840, 2400],
}


def _xp_to_level(xp: float, table: list[int], max_level: int = 50) -> int:
    """Convert raw XP to a level using a cumulative XP table."""
    level = 0
    for i, req in enumerate(table):
        if i > max_level:
            break
        if xp >= req:
            level = i
        else:
            break
    return min(level, max_level)


def _xp_to_level_progress(xp: float, table: list[int], max_level: int = 50) -> tuple[int, float]:
    """Convert raw XP to level + progress percentage toward next level."""
    level = _xp_to_level(xp, table, max_level)
    if level >= max_level or level >= len(table):
        return level, 100.0
    current_req = table[level - 1] if level > 0 else 0
    next_req = table[level] if level < len(table) else current_req
    diff = next_req - current_req
    if diff <= 0:
        return level, 100.0
    progress = (xp - current_req) / diff * 100
    return level, round(min(progress, 100.0), 1)


class PlayerStatsParser:

    @staticmethod
    def get_magical_power(profile_data: dict, uuid: str) -> dict:
        """Parse Magical Power, Power Stone, and Tuning.
        Path: member.accessory_bag_storage
        """
        member = profile_data.get("members", {}).get(uuid, {})
        acc_bag = member.get("accessory_bag_storage", {})

        true_mp = acc_bag.get("highest_magical_power", 0)
        power = acc_bag.get("selected_power", "None")

        tuning_data = acc_bag.get("tuning", {}).get("slot_0", {})
        tuning_pts = sum(tuning_data.values()) if isinstance(tuning_data, dict) else 0

        return {
            "mp": true_mp,
            "power": power.replace("_", " ").title() if isinstance(power, str) else str(power),
            "tuning_points": tuning_pts,
        }

    @staticmethod
    def get_fishing_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Fishing level, SC kills, and Trophy Fish.
        Paths: member.player_data.experience.SKILL_FISHING, member.trophy_fish
        """
        member = profile_data.get("members", {}).get(uuid, {})

        # Fishing XP (v2 path)
        exp = member.get("player_data", {}).get("experience", {}).get("SKILL_FISHING", 0)
        level = _xp_to_level(exp, SKILL_XP_TABLE, 50)

        # Trophy fish
        trophy_fish = member.get("trophy_fish", {})
        total_trophy = trophy_fish.get("total_caught", 0)

        # Sea creatures killed — aggregate from bestiary
        bestiary = member.get("bestiary", {})
        bestiary_kills = bestiary.get("kills", {})
        sea_creature_names = [
            "squid", "sea_walker", "night_squid", "sea_guardian",
            "sea_witch", "sea_archer", "rider_of_the_deep", "catfish",
            "sea_leech", "guardian_defender", "deep_sea_protector",
            "water_hydra", "sea_emperor", "agarimoo",
        ]
        sc_kills = 0
        for mob in sea_creature_names:
            sc_kills += bestiary_kills.get(f"kills_{mob}", 0)

        return {
            "level": level,
            "xp": exp,
            "sc_kills": sc_kills,
            "trophy_fish_caught": total_trophy,
        }

    @staticmethod
    def get_slayer_stats(profile_data: dict, uuid: str, boss: str) -> dict | None:
        """Parse Slayer stats for a specific boss.
        Path: member.slayer.slayer_bosses.<type>
        """
        boss_lower = boss.lower()
        member = profile_data.get("members", {}).get(uuid, {})
        slayer_data = member.get("slayer", {}).get("slayer_bosses", {}).get(boss_lower, {})

        if not slayer_data:
            return None

        xp = slayer_data.get("xp", 0)

        # Calculate level from XP table
        reqs = SLAYER_XP_TABLE.get(boss_lower, SLAYER_XP_TABLE["zombie"])
        level = 0
        for i, req in enumerate(reqs):
            if xp >= req:
                level = i + 1

        kills = sum(
            slayer_data.get(f"boss_kills_tier_{t}", 0)
            for t in range(5)
        )

        return {
            "boss": boss.title(),
            "level": level,
            "xp": xp,
            "kills": kills,
        }

    @staticmethod
    def get_all_slayers(profile_data: dict, uuid: str) -> list[dict]:
        """Get stats for all slayer bosses."""
        bosses = ["zombie", "spider", "wolf", "enderman", "blaze", "vampire"]
        results = []
        for boss in bosses:
            stats = PlayerStatsParser.get_slayer_stats(profile_data, uuid, boss)
            if stats and stats["xp"] > 0:
                results.append(stats)
        return results

    @staticmethod
    def get_bestiary_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Bestiary milestones.
        Path: member.bestiary
        """
        member = profile_data.get("members", {}).get(uuid, {})
        bestiary = member.get("bestiary", {})
        kills_data = bestiary.get("kills", {})

        # Count total unique mobs killed and total kills
        total_mobs = 0
        total_kills = 0
        lowest_mobs = []

        for key, count in kills_data.items():
            if key.startswith("kills_"):
                mob_name = key.replace("kills_", "").replace("_", " ").title()
                total_mobs += 1
                total_kills += count
                lowest_mobs.append((mob_name, count))

        # Sort by lowest kills to recommend easiest milestones
        lowest_mobs.sort(key=lambda x: x[1])
        recommendations = []
        for mob_name, count in lowest_mobs[:5]:
            # Bestiary milestones are at 10, 25, 100, 250, 1000, 2500, etc.
            milestones = [10, 25, 100, 250, 1000, 2500, 5000, 10000]
            next_ms = None
            for ms in milestones:
                if count < ms:
                    next_ms = ms
                    break
            if next_ms:
                remaining = next_ms - count
                recommendations.append(f"{mob_name} — {remaining:,} kills to next milestone")

        milestone_level = total_mobs // 10  # Rough milestone calc

        return {
            "milestone": milestone_level,
            "total_mobs": total_mobs,
            "total_kills": total_kills,
            "recommendations": recommendations if recommendations else ["No bestiary data found."],
        }

    @staticmethod
    def get_skills(profile_data: dict, uuid: str) -> dict:
        """Get all skill levels and skill average.
        Path: member.player_data.experience.SKILL_<NAME>
        """
        member = profile_data.get("members", {}).get(uuid, {})
        experience = member.get("player_data", {}).get("experience", {})

        skills_map = {
            "Farming": "SKILL_FARMING",
            "Mining": "SKILL_MINING",
            "Combat": "SKILL_COMBAT",
            "Foraging": "SKILL_FORAGING",
            "Fishing": "SKILL_FISHING",
            "Enchanting": "SKILL_ENCHANTING",
            "Alchemy": "SKILL_ALCHEMY",
            "Taming": "SKILL_TAMING",
            "Carpentry": "SKILL_CARPENTRY",
        }

        skills = {}
        total_levels = 0
        for display_name, api_key in skills_map.items():
            xp = experience.get(api_key, 0)
            level = _xp_to_level(xp, SKILL_XP_TABLE, 60)
            skills[display_name] = {"level": level, "xp": xp}
            total_levels += level

        sa = round(total_levels / len(skills_map), 2)

        return {
            "skills": skills,
            "skill_average": sa,
        }

    @staticmethod
    def get_skills_average(profile_data: dict, uuid: str) -> float:
        """Shortcut to just get the skill average number."""
        return PlayerStatsParser.get_skills(profile_data, uuid)["skill_average"]

    @staticmethod
    def get_dungeons_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Dungeons Catacombs and Class levels.
        Path: member.dungeons
        """
        member = profile_data.get("members", {}).get(uuid, {})
        dungeons = member.get("dungeons", {})

        # Catacombs level
        cata_exp = dungeons.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)
        cata_level = _xp_to_level(cata_exp, DUNGEON_XP_TABLE, 50)

        # Class levels
        classes = dungeons.get("player_classes", {})
        parsed_classes = {}
        for c_name, c_data in classes.items():
            if isinstance(c_data, dict):
                exp = c_data.get("experience", 0)
                parsed_classes[c_name.title()] = _xp_to_level(exp, DUNGEON_XP_TABLE, 50)

        # Selected class
        selected_class = dungeons.get("selected_dungeon_class", "None")

        # Floor completions
        floors = dungeons.get("dungeon_types", {}).get("catacombs", {}).get("tier_completions", {})
        total_completions = sum(floors.values()) if isinstance(floors, dict) else 0

        # Master mode completions
        master_floors = dungeons.get("dungeon_types", {}).get("master_catacombs", {}).get("tier_completions", {})
        master_completions = sum(master_floors.values()) if isinstance(master_floors, dict) else 0

        return {
            "catacombs_level": cata_level,
            "catacombs_xp": cata_exp,
            "classes": parsed_classes,
            "selected_class": selected_class.title() if isinstance(selected_class, str) else "None",
            "total_completions": total_completions,
            "master_completions": master_completions,
        }

    @staticmethod
    def calculate_networth(profile_data: dict, uuid: str) -> dict:
        """Calculate Networth.
        Paths: member.currencies.coin_purse, profile.banking.balance
        Note: True item networth requires NBT parsing. This is a simplified version.
        """
        member = profile_data.get("members", {}).get(uuid, {})
        purse = member.get("currencies", {}).get("coin_purse", 0)
        bank = profile_data.get("banking", {}).get("balance", 0)

        # Simplified item estimation (would need NBT parsing + item price DB for real values)
        # We flag this as an estimate
        return {
            "total": purse + bank,
            "purse": purse,
            "bank": bank,
            "items": 0,
            "is_estimate": True,
        }

    @staticmethod
    def get_accessories_list(profile_data: dict, uuid: str) -> dict:
        """Get accessory overview for /accessories command.
        Path: member.accessory_bag_storage
        """
        member = profile_data.get("members", {}).get(uuid, {})
        acc_bag = member.get("accessory_bag_storage", {})

        mp = acc_bag.get("highest_magical_power", 0)
        power = acc_bag.get("selected_power", "None")
        bag_upgrades = acc_bag.get("bag_upgrades_purchased", 0)

        tuning = acc_bag.get("tuning", {})
        tuning_summary = {}
        slot_0 = tuning.get("slot_0", {})
        for stat, val in slot_0.items():
            if val > 0:
                tuning_summary[stat.replace("_", " ").title()] = val

        return {
            "mp": mp,
            "power": power.replace("_", " ").title() if isinstance(power, str) else str(power),
            "bag_upgrades": bag_upgrades,
            "tuning": tuning_summary,
        }
