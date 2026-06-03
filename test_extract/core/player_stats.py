"""Player Stats Parsers.

Parses raw Hypixel API profile data into readable stats for Dungeons,
Skills, Slayer, Bestiary, Fishing, and Accessories (MP).
"""

from typing import Any


class PlayerStatsParser:
    
    @staticmethod
    def get_magical_power(profile_data: dict, uuid: str) -> dict:
        """Parse Magical Power, Power Stone, and Tuning."""
        member = profile_data.get("members", {}).get(uuid, {})
        acc_bag = member.get("accessory_bag_storage", {})
        
        # The true MP is now officially provided by Hypixel API
        true_mp = acc_bag.get("highest_magical_power", 0)
        power = acc_bag.get("selected_power", "None")
        
        # Tuning is a dict inside accessory_bag_storage -> tuning -> slot_0
        tuning_data = acc_bag.get("tuning", {}).get("slot_0", {})
        tuning_pts = sum(tuning_data.values()) if isinstance(tuning_data, dict) else 0
        
        return {
            "mp": true_mp,
            "power": power.replace("_", " ").title() if isinstance(power, str) else str(power),
            "tuning_points": tuning_pts
        }

    @staticmethod
    def get_fishing_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Fishing level, SC kills, and Trophy Fish."""
        member = profile_data.get("members", {}).get(uuid, {})
        stats = member.get("stats", {})
        
        sc_kills = stats.get("pet_milestone_sea_creatures_killed", 0)
        
        # Level approximation (Option A placeholder)
        exp = member.get("experience_skill_fishing", 0)
        level = int(exp ** 0.3) if exp > 0 else 0 
        
        trophy_fish = member.get("trophy_fish", {})
        total_trophy = trophy_fish.get("total_caught", 0)
        
        return {
            "level": min(level, 50),
            "xp": exp,
            "sc_kills": sc_kills,
            "trophy_fish_caught": total_trophy
        }

    @staticmethod
    def get_slayer_stats(profile_data: dict, uuid: str, boss: str) -> dict | None:
        """Parse Slayer stats for a specific boss (e.g. 'zombie', 'spider', 'wolf', 'enderman', 'blaze', 'vampire')."""
        boss_lower = boss.lower()
        member = profile_data.get("members", {}).get(uuid, {})
        slayer_data = member.get("slayer_bosses", {}).get(boss_lower, {})
        
        if not slayer_data:
            return None
            
        xp = slayer_data.get("xp", 0)
        # Approximate level logic for Option A
        level = 0
        reqs = [10, 30, 250, 1500, 5000, 20000, 100000, 400000, 1000000]
        for i, req in enumerate(reqs):
            if xp >= req:
                level = i + 1
                
        kills = slayer_data.get("boss_kills_tier_0", 0) + slayer_data.get("boss_kills_tier_1", 0) + slayer_data.get("boss_kills_tier_2", 0) + slayer_data.get("boss_kills_tier_3", 0) + slayer_data.get("boss_kills_tier_4", 0)
        
        return {
            "boss": boss.title(),
            "level": level,
            "xp": xp,
            "kills": kills
        }

    @staticmethod
    def get_bestiary_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Bestiary milestones."""
        member = profile_data.get("members", {}).get(uuid, {})
        bestiary = member.get("bestiary", {})
        
        # Option A Placeholder: Generate dummy recommendations 
        kills = bestiary.get("kills", {})
        milestone = len(kills.keys()) // 5  # Fake logic
        
        return {
            "milestone": milestone,
            "recommendations": [
                "Zombie (Graveyard) - 10 kills left",
                "Crypt Ghoul - 45 kills left",
                "Zealot - 120 kills left"
            ]
        }

    @staticmethod
    def get_skills_average(profile_data: dict, uuid: str) -> float:
        """Calculate Skill Average."""
        member = profile_data.get("members", {}).get(uuid, {})
        skills = [
            "farming", "mining", "combat", "foraging", "fishing",
            "enchanting", "alchemy", "taming", "carpentry"
        ]
        
        total_levels = 0
        for skill in skills:
            exp = member.get(f"experience_skill_{skill}", 0)
            # Dummy level calc for Option A
            level = min(int(exp ** 0.3) if exp > 0 else 0, 50)
            total_levels += level
            
        return round(total_levels / len(skills), 2)

    @staticmethod
    def get_dungeons_stats(profile_data: dict, uuid: str) -> dict:
        """Parse Dungeons Catacombs and Class levels."""
        member = profile_data.get("members", {}).get(uuid, {})
        dungeons = member.get("dungeons", {})
        
        cata_exp = dungeons.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)
        cata_level = min(int(cata_exp ** 0.3) if cata_exp > 0 else 0, 50)
        
        classes = dungeons.get("player_classes", {})
        parsed_classes = {}
        for c_name, c_data in classes.items():
            exp = c_data.get("experience", 0)
            parsed_classes[c_name.title()] = min(int(exp ** 0.3) if exp > 0 else 0, 50)
            
        floors = dungeons.get("dungeon_types", {}).get("catacombs", {}).get("tier_completions", {})
        total_completions = sum(floors.values())
        
        return {
            "catacombs_level": cata_level,
            "classes": parsed_classes,
            "total_completions": total_completions
        }

    @staticmethod
    def calculate_networth(profile_data: dict, uuid: str) -> dict:
        """Calculate simple Networth (Option A Placeholder)."""
        member = profile_data.get("members", {}).get(uuid, {})
        purse = member.get("coin_purse", 0)
        bank = profile_data.get("banking", {}).get("balance", 0)
        
        # For Option A, we use a random multiplier to simulate item networth
        simulated_item_nw = (purse + bank) * 2.5 + 50000000 
        
        total = purse + bank + simulated_item_nw
        
        return {
            "total": total,
            "purse": purse,
            "bank": bank,
            "items": simulated_item_nw
        }
