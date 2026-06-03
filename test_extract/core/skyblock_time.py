"""Skyblock Time and Event Calculator.

Provides helpers to calculate current in-game time, seasons, and predict
upcoming events like Spooky Festival, Jerry Pond, and Shark Scale.
"""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class SkyblockEvent:
    name: str
    description: str
    starts_in_seconds: int
    duration_seconds: int


class SkyblockTimeCalculator:
    # Skyblock year 0 started approximately at Unix Timestamp 1560275700
    YEAR_ZERO = 1560275700
    
    # Time constants in real-world seconds
    SB_HOUR = 50
    SB_DAY = 1200  # 20 minutes
    SB_MONTH = 37200  # 31 days
    SB_YEAR = 446400  # 12 months

    SEASONS = [
        "Spring (Early)", "Spring (Mid)", "Spring (Late)",
        "Summer (Early)", "Summer (Mid)", "Summer (Late)",
        "Autumn (Early)", "Autumn (Mid)", "Autumn (Late)",
        "Winter (Early)", "Winter (Mid)", "Winter (Late)"
    ]

    @classmethod
    def get_current_time(cls) -> dict:
        """Calculate the current Skyblock time from real time."""
        now = time.time()
        elapsed = now - cls.YEAR_ZERO
        
        # Calculate Skyblock units
        years = int(elapsed // cls.SB_YEAR)
        rem = elapsed % cls.SB_YEAR
        
        months = int(rem // cls.SB_MONTH)
        rem = rem % cls.SB_MONTH
        
        days = int(rem // cls.SB_DAY)
        rem = rem % cls.SB_DAY
        
        hours = int(rem // cls.SB_HOUR)
        
        season = cls.SEASONS[months] if 0 <= months < 12 else "Unknown"
        time_str = f"{hours:02d}:00"
        
        return {
            "year": years + 1,
            "month_name": season,
            "month_index": months + 1,
            "day": days + 1,
            "time": time_str
        }

    @classmethod
    def get_upcoming_events(cls) -> list[SkyblockEvent]:
        """Predict upcoming events. 
        
        Note: These are simplified placeholder calculations for Option A.
        In a full implementation, this would use exact Skyblock calendar logic.
        """
        now = time.time()
        elapsed = now - cls.YEAR_ZERO
        rem_year = elapsed % cls.SB_YEAR
        
        events = []
        
        # Spooky Festival is Autumn Late (Month 9), Days 29-31.
        spooky_start = 331200
        starts_in = spooky_start - rem_year if rem_year < spooky_start else (cls.SB_YEAR - rem_year) + spooky_start
        events.append(SkyblockEvent(
            name="🎃 Spooky Festival",
            description="Catch spooky sea creatures and get candy!",
            starts_in_seconds=int(starts_in),
            duration_seconds=1200 * 3
        ))
        
        # Season of the Jerry (Winter Late)
        jerry_start = 11 * 37200
        starts_in = jerry_start - rem_year if rem_year < jerry_start else (cls.SB_YEAR - rem_year) + jerry_start
        events.append(SkyblockEvent(
            name="❄️ Season of the Jerry",
            description="Jerry pond fishing and gifts!",
            starts_in_seconds=int(starts_in),
            duration_seconds=37200
        ))
        
        # Dark Auction (Every 3 in-game days = every 1 hour IRL)
        # 1 IRL hour = 3600 seconds.
        da_starts_in = 3600 - (now % 3600)
        events.append(SkyblockEvent(
            name="🌑 Dark Auction",
            description="Sirius is selling rare items in the dark forest.",
            starts_in_seconds=int(da_starts_in),
            duration_seconds=600
        ))
        
        # Jacob's Farming Contest (Every 3 in-game days, offset by 1 day)
        jacob_starts_in = 3600 - ((now + 1200) % 3600)
        events.append(SkyblockEvent(
            name="🌾 Jacob's Farming Contest",
            description="Harvest crops to win medals and tickets!",
            starts_in_seconds=int(jacob_starts_in),
            duration_seconds=1200
        ))
        
        # Marina Fishing Festival (Placeholder)
        events.append(SkyblockEvent(
            name="🦈 Fishing Festival",
            description="Catch sharks during Marina's festival.",
            starts_in_seconds=int((now % 86400) / 2),
            duration_seconds=3600
        ))
        
        events.sort(key=lambda e: e.starts_in_seconds)
        return events
