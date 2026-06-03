"""Auction BIN scanner with batched page fetching and in-memory cache."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.hypixel_client import HypixelClient
    from storage.database import Database

logger = logging.getLogger(__name__)


@dataclass
class AuctionItem:
    """A single Buy-It-Now (BIN) auction listing.

    Attributes
    ----------
    uuid:
        Unique auction identifier.
    item_name:
        Human-readable item name.
    tier:
        Rarity tier (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC, …).
    bin_price:
        BIN price in coins.
    category:
        Auction house category (e.g. ``weapon``, ``armor``).
    """

    uuid: str
    item_name: str
    tier: str
    bin_price: int
    category: str


class AuctionCache:
    """In-memory cache for lowest BIN prices across the auction house.

    Fetches all pages in batches to stay within rate limits and stores
    the results in the database for historical averaging.

    Parameters
    ----------
    client:
        An initialised :class:`HypixelClient`.
    db:
        An initialised :class:`Database`.
    ttl:
        Time-to-live in seconds before the cache is considered stale.
    """

    BATCH_SIZE: int = 5  # concurrent page fetches per batch

    def __init__(self, client: HypixelClient, db: Database, ttl: int = 120) -> None:
        self.client = client
        self.db = db
        self.ttl = ttl
        self._lowest_bins: dict[str, int] | None = None
        self._last_fetch: float = 0.0

    async def get(self) -> dict[str, int]:
        """Return cached lowest-BIN mapping, refreshing if stale.

        Returns
        -------
        dict[str, int]
            Mapping of ``item_name`` → lowest BIN price.
        """
        now = time.time()
        if self._lowest_bins is not None and (now - self._last_fetch) < self.ttl:
            logger.debug(
                "Returning cached auction data (%d items)", len(self._lowest_bins)
            )
            return self._lowest_bins

        logger.info("Auction cache stale — fetching all BIN pages")
        self._lowest_bins = await self._fetch_all_bins()
        self._last_fetch = time.time()
        return self._lowest_bins

    async def _fetch_all_bins(self) -> dict[str, int]:
        """Fetch every auction page, extract BINs, and keep only the lowest.

        Returns
        -------
        dict[str, int]
            Mapping of ``item_name`` → lowest BIN price.
        """
        first_page: dict[str, Any] = await self.client.get_auctions(page=0)
        total_pages: int = first_page.get("totalPages", 1)
        logger.info("Auction house has %d pages", total_pages)

        all_items: list[AuctionItem] = self._parse_page(first_page)

        # Fetch remaining pages in batches to avoid rate-limit bursts
        for batch_start in range(1, total_pages, self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, total_pages)
            tasks = [
                self.client.get_auctions(page=p) for p in range(batch_start, batch_end)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Failed to fetch auction page: %s", result)
                    continue
                all_items.extend(self._parse_page(result))

        logger.info("Collected %d total BIN items across %d pages", len(all_items), total_pages)

        # Reduce to lowest BIN per item name
        lowest: dict[str, int] = {}
        for item in all_items:
            if item.item_name not in lowest or item.bin_price < lowest[item.item_name]:
                lowest[item.item_name] = item.bin_price

        # Persist to database for historical averaging
        await self.db.store_auctions(lowest)

        logger.info("Stored %d unique lowest-BIN entries", len(lowest))
        return lowest

    def _parse_page(self, page_data: dict[str, Any]) -> list[AuctionItem]:
        """Extract BIN-only listings from a single auction page.

        Parameters
        ----------
        page_data:
            Raw JSON response from ``/skyblock/auctions``.

        Returns
        -------
        list[AuctionItem]
            BIN auction items found on this page.
        """
        items: list[AuctionItem] = []
        for auction in page_data.get("auctions", []):
            if auction.get("bin", False):
                items.append(
                    AuctionItem(
                        uuid=auction["uuid"],
                        item_name=auction.get("item_name", "Unknown"),
                        tier=auction.get("tier", "COMMON"),
                        bin_price=auction.get("starting_bid", 0),
                        category=auction.get("category", "unknown"),
                    )
                )
        return items
