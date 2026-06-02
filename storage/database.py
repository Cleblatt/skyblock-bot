"""Async SQLite database for storing historical Bazaar and Auction data."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database layer.

    Stores time-series snapshots of Bazaar prices and Auction lowest-BIN
    prices for historical analysis and flip detection.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Parent directories are
        created automatically on :meth:`initialize`.
    """

    def __init__(self, db_path: str = "./data/skyblock.db") -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Open the database connection and create tables if needed."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()
        logger.info("Database initialised at %s", self.db_path)

    async def _create_tables(self) -> None:
        """Create the schema and indices if they do not already exist."""
        assert self._db is not None

        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS bazaar_history (
                timestamp    REAL    NOT NULL,
                product_id   TEXT    NOT NULL,
                buy_price    REAL    NOT NULL,
                sell_price   REAL    NOT NULL,
                volume_week  INTEGER NOT NULL
            )
            """
        )

        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS auction_history (
                timestamp   REAL    NOT NULL,
                item_name   TEXT    NOT NULL,
                lowest_bin  INTEGER NOT NULL
            )
            """
        )

        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_bazaar_ts ON bazaar_history(timestamp)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_bazaar_pid ON bazaar_history(product_id)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_ts ON auction_history(timestamp)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_name ON auction_history(item_name)"
        )

        await self._db.commit()
        logger.debug("Database tables and indices verified")

    # ------------------------------------------------------------------ #
    # Write helpers
    # ------------------------------------------------------------------ #

    async def store_bazaar(self, products: list[Any]) -> None:
        """Insert a snapshot of Bazaar products into the history table.

        Parameters
        ----------
        products:
            List of :class:`~core.bazaar.BazaarProduct` instances.
        """
        assert self._db is not None
        now = time.time()
        rows = [
            (now, p.product_id, p.buy_price, p.sell_price, p.moving_week)
            for p in products
        ]
        await self._db.executemany(
            "INSERT INTO bazaar_history VALUES (?, ?, ?, ?, ?)", rows
        )
        await self._db.commit()
        logger.debug("Stored %d bazaar products at ts=%.0f", len(rows), now)

    async def store_auctions(self, bins: dict[str, int]) -> None:
        """Insert a snapshot of lowest-BIN auction prices.

        Parameters
        ----------
        bins:
            Mapping of ``item_name`` → lowest BIN price.
        """
        assert self._db is not None
        now = time.time()
        rows = [(now, name, price) for name, price in bins.items()]
        await self._db.executemany(
            "INSERT INTO auction_history VALUES (?, ?, ?)", rows
        )
        await self._db.commit()
        logger.debug("Stored %d auction BIN entries at ts=%.0f", len(rows), now)

    # ------------------------------------------------------------------ #
    # Read helpers
    # ------------------------------------------------------------------ #

    async def get_bazaar_avg(
        self, product_id: str, hours: int = 24
    ) -> tuple[float, float]:
        """Return average buy/sell prices over a time window.

        Parameters
        ----------
        product_id:
            Bazaar product identifier (e.g. ``ENCHANTED_DIAMOND``).
        hours:
            Look-back window in hours.

        Returns
        -------
        tuple[float, float]
            ``(avg_buy_price, avg_sell_price)``.  Returns ``(0.0, 0.0)``
            if no data is available.
        """
        assert self._db is not None
        cutoff = time.time() - (hours * 3600)
        cursor = await self._db.execute(
            "SELECT AVG(buy_price), AVG(sell_price) "
            "FROM bazaar_history "
            "WHERE product_id = ? AND timestamp > ?",
            (product_id, cutoff),
        )
        row = await cursor.fetchone()
        if row and row[0] is not None:
            return (row[0], row[1])
        return (0.0, 0.0)

    async def get_auction_avg(self, item_name: str, hours: int = 24) -> float:
        """Return average lowest-BIN price over a time window.

        Parameters
        ----------
        item_name:
            Auction item name.
        hours:
            Look-back window in hours.

        Returns
        -------
        float
            Average lowest BIN price, or ``0.0`` if no data is available.
        """
        assert self._db is not None
        cutoff = time.time() - (hours * 3600)
        cursor = await self._db.execute(
            "SELECT AVG(lowest_bin) "
            "FROM auction_history "
            "WHERE item_name = ? AND timestamp > ?",
            (item_name, cutoff),
        )
        row = await cursor.fetchone()
        if row and row[0] is not None:
            return row[0]
        return 0.0

    # ------------------------------------------------------------------ #
    # Maintenance
    # ------------------------------------------------------------------ #

    async def cleanup(self, days: int = 7) -> int:
        """Delete rows older than *days*.

        Parameters
        ----------
        days:
            Retention period in days.

        Returns
        -------
        int
            Total number of rows deleted across both tables.
        """
        assert self._db is not None
        cutoff = time.time() - (days * 86400)

        cursor = await self._db.execute(
            "DELETE FROM bazaar_history WHERE timestamp < ?", (cutoff,)
        )
        count_bazaar = cursor.rowcount

        cursor = await self._db.execute(
            "DELETE FROM auction_history WHERE timestamp < ?", (cutoff,)
        )
        count_auction = cursor.rowcount

        await self._db.commit()
        total = count_bazaar + count_auction
        logger.info(
            "Cleanup removed %d rows (%d bazaar, %d auction)",
            total,
            count_bazaar,
            count_auction,
        )
        return total

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            logger.debug("Database connection closed")
