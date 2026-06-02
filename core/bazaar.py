"""Bazaar data parser and in-memory cache backed by historical DB storage."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.hypixel_client import HypixelClient
    from storage.database import Database

logger = logging.getLogger(__name__)


@dataclass
class BazaarProduct:
    """Snapshot of a single Bazaar product's quick-status data.

    Attributes
    ----------
    buy_price:
        Instant-sell price (what a seller receives).
    sell_price:
        Instant-buy price (what a buyer pays).
    spread:
        ``sell_price - buy_price`` — the raw coin difference.
    spread_pct:
        ``spread / buy_price * 100`` — margin as a percentage.
    """

    product_id: str
    buy_price: float
    sell_price: float
    buy_volume: int
    sell_volume: int
    buy_orders: int
    sell_orders: int
    moving_week: int
    spread: float = field(init=False)
    spread_pct: float = field(init=False)

    def __post_init__(self) -> None:
        self.spread = self.sell_price - self.buy_price
        if self.buy_price > 0:
            self.spread_pct = self.spread / self.buy_price * 100
        else:
            self.spread_pct = 0.0


class BazaarCache:
    """In-memory cache for Bazaar product data.

    Fetches from the Hypixel API when the cache is stale and persists
    each snapshot to the database for historical analysis.

    Parameters
    ----------
    client:
        An initialised :class:`HypixelClient`.
    db:
        An initialised :class:`Database`.
    ttl:
        Time-to-live in seconds before the cache is considered stale.
    """

    def __init__(self, client: HypixelClient, db: Database, ttl: int = 60) -> None:
        self.client = client
        self.db = db
        self.ttl = ttl
        self._data: dict[str, BazaarProduct] | None = None
        self._last_fetch: float = 0.0

    async def get(self) -> dict[str, BazaarProduct]:
        """Return cached Bazaar data, refreshing if stale.

        Returns
        -------
        dict[str, BazaarProduct]
            Mapping of product ID to its :class:`BazaarProduct`.
        """
        now = time.time()
        if self._data is not None and (now - self._last_fetch) < self.ttl:
            logger.debug("Returning cached bazaar data (%d products)", len(self._data))
            return self._data

        logger.info("Bazaar cache stale — fetching fresh data")
        self._data = await self._fetch_and_parse()
        self._last_fetch = time.time()
        return self._data

    async def _fetch_and_parse(self) -> dict[str, BazaarProduct]:
        """Fetch Bazaar data from the API, parse it, and store to DB.

        Returns
        -------
        dict[str, BazaarProduct]
            Freshly-parsed product mapping.
        """
        raw: dict[str, Any] = await self.client.get_bazaar()
        products: dict[str, BazaarProduct] = {}

        for pid, pdata in raw.get("products", {}).items():
            qs = pdata.get("quick_status", {})
            products[pid] = BazaarProduct(
                product_id=pid,
                buy_price=qs.get("buyPrice", 0.0),
                sell_price=qs.get("sellPrice", 0.0),
                buy_volume=qs.get("buyVolume", 0),
                sell_volume=qs.get("sellVolume", 0),
                buy_orders=qs.get("buyOrders", 0),
                sell_orders=qs.get("sellOrders", 0),
                moving_week=qs.get("buyMovingWeek", 0) + qs.get("sellMovingWeek", 0),
            )

        logger.info("Parsed %d bazaar products", len(products))

        # Persist snapshot to the database for historical analysis
        await self.db.store_bazaar(list(products.values()))
        return products
