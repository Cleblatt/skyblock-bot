import asyncio
import os
from core.hypixel_client import HypixelClient
from core.mojang_client import MojangClient
from core.player_stats import PlayerStatsParser
from utils.helpers import get_profile

class DummyBot:
    def __init__(self):
        self.mojang = MojangClient()
        self.hypixel = HypixelClient("4f529778-a7e0-4bf7-9b9c-8dc5a64bf4d3")

async def test():
    bot = DummyBot()
    try:
        print("Testing Default Selected Profile:")
        uuid, display_name, selected = await get_profile(bot, "Cleblatt")
        print(f"Selected profile ID: {selected['profile_id']} (Cute name: {selected.get('cute_name')})")

        print("\nTesting Named Profile (Pineapple):")
        uuid, display_name, pineapple = await get_profile(bot, "Cleblatt", "Pineapple")
        print(f"Profile ID: {pineapple['profile_id']} (Cute name: {pineapple.get('cute_name')})")
        
        print("\nTesting Unknown Profile (Apple):")
        try:
            await get_profile(bot, "Cleblatt", "Apple")
        except Exception as e:
            print(f"Expected Error: {e}")

    finally:
        await bot.mojang.close()
        await bot.hypixel.close()

asyncio.run(test())
