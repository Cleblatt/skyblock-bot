"""Fully async Hypixel API client with rate-limit tracking and exponential backoff."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class HypixelAPIError(Exception):
    """Raised when the Hypixel API returns an unsuccessful response."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(f"[HTTP {status_code}] {message}")


class HypixelClient:
    """Async wrapper around the Hypixel SkyBlock API.

    Parameters
    ----------
    api_key:
        Your Hypixel developer API key.
    base_url:
        Base URL for the Hypixel API (default v2).
    """

    MAX_RETRIES: int = 3
    RETRY_DELAYS: tuple[float, ...] = (1.0, 4.0, 16.0)
    REQUEST_TIMEOUT: float = 15.0
    RATE_LIMIT_THRESHOLD: int = 10

    def __init__(self, api_key: str, base_url: str = "https://api.hypixel.net/v2") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        self._rate_limit_remaining: int | None = None
        logger.debug("HypixelClient initialised (base_url=%s)", self.base_url)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Create the ``aiohttp.ClientSession`` lazily on first use."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"API-Key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT),
            )
            logger.debug("Created new aiohttp session")
        return self._session

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        """Send a GET request with retry logic.

        Parameters
        ----------
        endpoint:
            API path appended to *base_url* (e.g. ``/skyblock/bazaar``).
        params:
            Optional query-string parameters.
        auth:
            If ``False`` the ``API-Key`` header is omitted (used for
            ``/resources/*`` endpoints).

        Returns
        -------
        dict
            The parsed JSON response body.

        Raises
        ------
        HypixelAPIError
            If the API signals ``success=false`` or all retries are exhausted.
        """
        session = await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        headers: dict[str, str] = {}
        if not auth:
            # Override the session-level API-Key header by sending an empty
            # headers dict so it doesn't get included automatically.  The
            # cleanest way is to craft a fresh request without the key.
            headers["API-Key"] = ""  # aiohttp still sends it; see below

        last_exc: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if not auth:
                    # Build a clean request without the API-Key header
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT),
                    ) as anon_session:
                        async with anon_session.get(url, params=params) as resp:
                            return await self._handle_response(resp)
                else:
                    # Throttle proactively when close to the rate limit
                    if (
                        self._rate_limit_remaining is not None
                        and self._rate_limit_remaining < self.RATE_LIMIT_THRESHOLD
                    ):
                        sleep_time = 1.0
                        logger.warning(
                            "Rate-limit low (%d remaining) — sleeping %.1fs",
                            self._rate_limit_remaining,
                            sleep_time,
                        )
                        await asyncio.sleep(sleep_time)

                    async with session.get(url, params=params) as resp:
                        # Track rate-limit header
                        remaining_header = resp.headers.get("RateLimit-Remaining")
                        if remaining_header is not None:
                            try:
                                self._rate_limit_remaining = int(remaining_header)
                            except ValueError:
                                pass

                        return await self._handle_response(resp)

            except (aiohttp.ClientResponseError, HypixelAPIError) as exc:
                last_exc = exc
                status = getattr(exc, "status_code", 0) or getattr(exc, "status", 0)
                if status == 429 or (isinstance(status, int) and status >= 500):
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.warning(
                        "Retryable error (HTTP %d) on %s — retrying in %.1fs (attempt %d/%d)",
                        status,
                        endpoint,
                        delay,
                        attempt + 1,
                        self.MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                logger.warning(
                    "Network error on %s: %s — retrying in %.1fs (attempt %d/%d)",
                    endpoint,
                    exc,
                    delay,
                    attempt + 1,
                    self.MAX_RETRIES,
                )
                await asyncio.sleep(delay)
                continue

        raise HypixelAPIError(
            f"All {self.MAX_RETRIES} retries exhausted for {endpoint}: {last_exc}",
            status_code=0,
        )

    async def _handle_response(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        """Parse and validate a response, raising on errors."""
        if resp.status == 429:
            raise HypixelAPIError("Rate limited by Hypixel API", status_code=429)
        if resp.status >= 500:
            raise HypixelAPIError(
                f"Server error: {resp.status}", status_code=resp.status
            )
        if resp.status != 200:
            text = await resp.text()
            raise HypixelAPIError(
                f"Unexpected status {resp.status}: {text}", status_code=resp.status
            )

        data: dict[str, Any] = await resp.json()
        if not data.get("success", True):
            cause = data.get("cause", "Unknown error")
            raise HypixelAPIError(cause, status_code=resp.status)

        return data

    # ------------------------------------------------------------------ #
    # Convenience endpoints
    # ------------------------------------------------------------------ #

    async def get_bazaar(self) -> dict[str, Any]:
        """Fetch current Bazaar product listings."""
        logger.debug("Fetching bazaar data")
        return await self._request("/skyblock/bazaar")

    async def get_auctions(self, page: int = 0) -> dict[str, Any]:
        """Fetch a single page of active auctions."""
        logger.debug("Fetching auctions page %d", page)
        return await self._request("/skyblock/auctions", params={"page": page})

    async def get_auctions_ended(self) -> dict[str, Any]:
        """Fetch recently-ended auctions."""
        logger.debug("Fetching ended auctions")
        return await self._request("/skyblock/auctions_ended")

    async def get_player_profiles(self, uuid: str) -> dict[str, Any]:
        """Fetch all SkyBlock profiles for a player UUID."""
        logger.debug("Fetching profiles for UUID %s", uuid)
        return await self._request("/skyblock/profiles", params={"uuid": uuid})

    async def get_collections_resource(self) -> dict[str, Any]:
        """Fetch the static collections resource (no auth required)."""
        logger.debug("Fetching collections resource")
        return await self._request("/resources/skyblock/collections", auth=False)

    async def get_items_resource(self) -> dict[str, Any]:
        """Fetch the static items resource (no auth required)."""
        logger.debug("Fetching items resource")
        return await self._request("/resources/skyblock/items", auth=False)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("aiohttp session closed")
