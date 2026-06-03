"""Async Mojang API client for resolving Minecraft usernames to UUIDs."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

# Matches a UUID with or without dashes (exactly 32 hex characters).
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
)


class PlayerNotFoundError(Exception):
    """Raised when a Minecraft player cannot be found via the Mojang API."""

    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Player not found: {username}")


class MojangClient:
    """Resolve Minecraft usernames to UUIDs using the Mojang API.

    Maintains an in-memory cache with a configurable TTL to minimise
    redundant API calls.

    Parameters
    ----------
    base_url:
        Base URL for the Mojang API.
    """

    CACHE_TTL: int = 3600  # seconds

    def __init__(self, base_url: str = "https://api.mojang.com") -> None:
        self.base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        # Cache: username_lower -> (uuid, display_name, expiry_timestamp)
        self._cache: dict[str, tuple[str, str, float]] = {}
        logger.debug("MojangClient initialised (base_url=%s)", self.base_url)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Create the ``aiohttp.ClientSession`` lazily on first use."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10.0),
            )
            logger.debug("Created new Mojang aiohttp session")
        return self._session

    @staticmethod
    def is_uuid(value: str) -> bool:
        """Return ``True`` if *value* looks like a Minecraft UUID.

        Accepts both dashed (``xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx``) and
        undashed (32 hex character) formats.
        """
        return bool(_UUID_RE.match(value))

    async def resolve(self, username_or_uuid: str) -> tuple[str, str]:
        """Resolve a username or UUID to ``(uuid, display_name)``.

        If the input is already a UUID it is normalised (dashes stripped)
        and returned immediately without an API call.

        Parameters
        ----------
        username_or_uuid:
            A Minecraft username *or* UUID string.

        Returns
        -------
        tuple[str, str]
            ``(uuid_no_dashes, display_name)``

        Raises
        ------
        PlayerNotFoundError
            If the Mojang API responds with 204 or 404.
        """
        # Fast-path: already a UUID — no API call needed.
        if self.is_uuid(username_or_uuid):
            clean_uuid = username_or_uuid.replace("-", "")
            logger.debug("Input is already a UUID: %s", clean_uuid)
            return (clean_uuid, username_or_uuid)

        # Check in-memory cache
        cache_key = username_or_uuid.lower()
        cached = self._cache.get(cache_key)
        if cached is not None:
            uuid, display_name, expiry = cached
            if time.time() < expiry:
                logger.debug("Cache hit for '%s' -> %s", username_or_uuid, uuid)
                return (uuid, display_name)
            else:
                logger.debug("Cache expired for '%s'", username_or_uuid)
                del self._cache[cache_key]

        # Call the Mojang API
        session = await self._ensure_session()
        url = f"{self.base_url}/users/profiles/minecraft/{username_or_uuid}"
        logger.debug("Resolving username '%s' via Mojang API", username_or_uuid)

        async with session.get(url) as resp:
            if resp.status in (204, 404):
                raise PlayerNotFoundError(username_or_uuid)

            if resp.status != 200:
                text = await resp.text()
                raise PlayerNotFoundError(
                    f"{username_or_uuid} (HTTP {resp.status}: {text})"
                )

            data: dict[str, Any] = await resp.json()

        uuid: str = data["id"]  # 32 hex chars, no dashes
        display_name: str = data["name"]

        # Store in cache
        self._cache[cache_key] = (uuid, display_name, time.time() + self.CACHE_TTL)
        logger.debug("Resolved '%s' -> uuid=%s, name=%s", username_or_uuid, uuid, display_name)

        return (uuid, display_name)

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Mojang aiohttp session closed")
