async def get_profile(bot, player: str, profile_name: str | None = None) -> tuple[str, str, dict]:
    """Resolve player and return (uuid, display_name, selected_profile)."""
    uuid, display_name = await bot.mojang.resolve(player)
    profiles_data = await bot.hypixel.get_player_profiles(uuid)
    profiles = profiles_data.get("profiles", [])
    
    if not profiles:
        raise ValueError(f"{display_name} has no Skyblock profiles.")
    
    if profile_name:
        for p in profiles:
            if p.get("cute_name", "").lower() == profile_name.lower():
                return uuid, display_name, p
        raise ValueError(f"Profile '{profile_name}' not found for {display_name}.")
    
    # Default to selected profile
    selected = next((p for p in profiles if p.get("selected", False)), profiles[0])
    return uuid, display_name, selected
