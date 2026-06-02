"""Market flip-detection engine for Bazaar and Auction data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.bazaar import BazaarProduct

if TYPE_CHECKING:
    from storage.database import Database

logger = logging.getLogger(__name__)


@dataclass
class FlipOpportunity:
    """A detected market arbitrage or flip opportunity.

    Attributes
    ----------
    item_name:
        Human-readable item name.
    source:
        ``'Bazaar'`` or ``'Auction'``.
    buy_price:
        Price to acquire the item.
    sell_price:
        Expected selling price.
    profit:
        ``sell_price - buy_price``.
    margin_pct:
        Profit margin as a percentage.
    volume:
        Weekly trading volume (Bazaar) or ``0`` (Auction).
    confidence:
        Emoji-labelled confidence level:
        ``'🟢 High'``, ``'🟡 Medium'``, or ``'🔴 Low'``.
    """

    item_name: str
    source: str  # 'Bazaar' or 'Auction'
    buy_price: float
    sell_price: float
    profit: float
    margin_pct: float
    volume: int  # weekly volume or estimated
    confidence: str  # emoji: '🟢 High', '🟡 Medium', '🔴 Low'


@dataclass
class CraftProfit:
    item_name: str
    craft_cost: float
    sell_price: float
    profit: float
    margin_pct: float
    recipe_str: str


class MarketAnalyzer:
    """Scans Bazaar and Auction data for profitable flip opportunities.

    Parameters
    ----------
    db:
        An initialised :class:`Database` for historical price lookups.
    min_margin_pct:
        Minimum margin percentage to qualify as a flip.
    min_profit:
        Minimum estimated profit in coins.
    top_count:
        Maximum number of results to return.
    """

    def __init__(
        self,
        db: Database,
        min_margin_pct: float = 10.0,
        min_profit: float = 50_000.0,
        top_count: int = 10,
    ) -> None:
        self.db = db
        self.min_margin_pct = min_margin_pct
        self.min_profit = min_profit
        self.top_count = top_count

    async def find_all_flips(
        self,
        bazaar_data: dict[str, BazaarProduct],
        auction_bins: dict[str, int],
    ) -> list[FlipOpportunity]:
        """Analyse both markets and return the most profitable flips.

        Parameters
        ----------
        bazaar_data:
            Current Bazaar product mapping.
        auction_bins:
            Current lowest-BIN mapping.

        Returns
        -------
        list[FlipOpportunity]
            Top flips sorted by profit (descending), capped at
            :attr:`top_count`.
        """
        bazaar_flips = await self._bazaar_flips(bazaar_data)
        auction_flips = await self._auction_flips(auction_bins)

        combined = bazaar_flips + auction_flips
        combined.sort(key=lambda f: f.profit, reverse=True)

        top = combined[: self.top_count]
        logger.info(
            "Found %d bazaar + %d auction flips → returning top %d",
            len(bazaar_flips),
            len(auction_flips),
            len(top),
        )
        return top

    async def get_best_bazaar_flips(self, bazaar_data: dict[str, BazaarProduct]) -> list[FlipOpportunity]:
        """Specific command helper for /flip_bz."""
        flips = await self._bazaar_flips(bazaar_data)
        flips.sort(key=lambda f: f.margin_pct, reverse=True)
        return flips[:self.top_count]

    async def get_best_auction_flips(self, auction_bins: dict[str, int]) -> list[FlipOpportunity]:
        """Specific command helper for /flip_ah."""
        flips = await self._auction_flips(auction_bins)
        flips.sort(key=lambda f: f.profit, reverse=True)
        return flips[:self.top_count]

    async def calculate_craft_profit(self, item_name: str, bazaar_data: dict[str, BazaarProduct], auction_bins: dict[str, int]) -> CraftProfit | None:
        """Calculate profit for crafting an item (Option A Placeholder)."""
        item_lower = item_name.lower()
        
        # Hardcoded recipes for Option A demonstration
        recipes = {
            "aspect of the end": {
                "ingredients": {"ENCHANTED_EYE_OF_ENDER": 32, "ENCHANTED_DIAMOND": 1},
                "output": "Aspect of the End"
            },
            "hot potato book": {
                "ingredients": {"ENCHANTED_BAKED_POTATO": 1, "PAPER": 3},
                "output": "Hot Potato Book"
            }
        }
        
        match = None
        for key, recipe in recipes.items():
            if item_lower in key:
                match = recipe
                break
                
        if not match:
            return None
            
        cost = 0.0
        recipe_parts = []
        for ing, amount in match["ingredients"].items():
            price = bazaar_data[ing].buy_price if ing in bazaar_data else 0
            cost += price * amount
            recipe_parts.append(f"{amount}x {ing.replace('_', ' ').title()}")
            
        sell_price = auction_bins.get(match["output"], 0)
        
        if sell_price == 0:
            # Fallback to bazaar sell price if it's a bazaar item
            sell_key = match["output"].upper().replace(" ", "_")
            if sell_key in bazaar_data:
                sell_price = bazaar_data[sell_key].sell_price
                
        profit = sell_price - cost
        margin = (profit / cost * 100) if cost > 0 else 0
        
        return CraftProfit(
            item_name=match["output"],
            craft_cost=cost,
            sell_price=sell_price,
            profit=profit,
            margin_pct=margin,
            recipe_str=", ".join(recipe_parts)
        )

    # ------------------------------------------------------------------ #
    # Bazaar flip detection
    # ------------------------------------------------------------------ #

    async def _bazaar_flips(
        self, products: dict[str, BazaarProduct]
    ) -> list[FlipOpportunity]:
        """Identify profitable Bazaar spread-based flips.

        A product qualifies when its spread percentage exceeds
        *min_margin_pct* and the estimated weekly bulk profit exceeds
        *min_profit*.
        """
        flips: list[FlipOpportunity] = []

        for pid, product in products.items():
            if product.buy_price <= 0 or product.sell_price <= 0:
                continue

            margin_pct = product.spread_pct
            profit = product.spread

            if margin_pct < self.min_margin_pct:
                continue
            if profit < 1:
                continue

            # Estimate bulk profit from weekly volume (capped at 1 000 units)
            estimated_weekly_profit = profit * min(product.moving_week, 1000)
            if estimated_weekly_profit < self.min_profit:
                continue

            # Determine confidence level
            if margin_pct > 20 and product.moving_week > 50_000:
                confidence = "🟢 High"
            elif margin_pct > 10 and product.moving_week > 10_000:
                confidence = "🟡 Medium"
            else:
                confidence = "🔴 Low"

            # Boost confidence if current spread exceeds historical average
            hist_buy, hist_sell = await self.db.get_bazaar_avg(pid)
            if hist_buy and hist_sell:
                hist_spread = hist_sell - hist_buy
                if product.spread > hist_spread * 1.5:
                    if confidence == "🟡 Medium":
                        confidence = "🟢 High"

            flips.append(
                FlipOpportunity(
                    item_name=pid.replace("_", " ").title(),
                    source="Bazaar",
                    buy_price=product.buy_price,
                    sell_price=product.sell_price,
                    profit=profit,
                    margin_pct=margin_pct,
                    volume=product.moving_week,
                    confidence=confidence,
                )
            )

        logger.debug("Detected %d bazaar flips", len(flips))
        return flips

    # ------------------------------------------------------------------ #
    # Auction flip detection
    # ------------------------------------------------------------------ #

    async def _auction_flips(
        self, current_bins: dict[str, int]
    ) -> list[FlipOpportunity]:
        """Identify underpriced BIN listings relative to historical averages.

        An item qualifies when the discount from its historical average
        exceeds *min_margin_pct* and the absolute profit exceeds
        *min_profit*.
        """
        flips: list[FlipOpportunity] = []

        for item_name, current_price in current_bins.items():
            if current_price <= 0:
                continue

            avg_price = await self.db.get_auction_avg(item_name)
            if not avg_price or avg_price <= 0:
                continue

            discount_pct = (avg_price - current_price) / avg_price * 100
            if discount_pct < self.min_margin_pct:
                continue

            profit = avg_price - current_price
            if profit < self.min_profit:
                continue

            if discount_pct > 25:
                confidence = "🟢 High"
            elif discount_pct > 15:
                confidence = "🟡 Medium"
            else:
                confidence = "🔴 Low"

            flips.append(
                FlipOpportunity(
                    item_name=item_name,
                    source="Auction",
                    buy_price=current_price,
                    sell_price=avg_price,
                    profit=profit,
                    margin_pct=discount_pct,
                    volume=0,
                    confidence=confidence,
                )
            )

        logger.debug("Detected %d auction flips", len(flips))
        return flips
