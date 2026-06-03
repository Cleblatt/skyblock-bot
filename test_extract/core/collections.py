"""Collection tier calculator and progress tracker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.hypixel_client import HypixelClient

logger = logging.getLogger(__name__)


@dataclass
class CollectionProgress:
    """Progress toward a single collection tier.

    Attributes
    ----------
    name:
        Human-readable collection name (e.g. ``Wheat``).
    item_id:
        Internal item identifier (e.g. ``WHEAT``).
    category:
        Lowercased category (e.g. ``farming``, ``mining``).
    current_amount:
        How many items the player has collected.
    current_tier:
        The highest tier the player has unlocked.
    max_tier:
        Maximum tier available for this collection.
    next_tier:
        The target tier being tracked (either next or a custom target).
    next_tier_req:
        Total items required to reach *next_tier*.
    remaining:
        Items still needed to reach *next_tier*.
    progress_pct:
        Percentage progress from *current_tier* toward *next_tier*.
    """

    name: str
    item_id: str
    category: str
    current_amount: int
    current_tier: int
    max_tier: int
    next_tier: int
    next_tier_req: int
    remaining: int
    progress_pct: float


class CollectionTracker:
    """Loads SkyBlock collection definitions and computes player progress.

    Parameters
    ----------
    client:
        An initialised :class:`HypixelClient` for fetching the static
        collections resource.
    """

    def __init__(self, client: HypixelClient) -> None:
        self.client = client
        self._definitions: dict[str, dict[str, Any]] | None = None
        self._item_id_to_name: dict[str, str] = {}

    async def load_definitions(self) -> None:
        """Fetch and cache collection definitions from the Hypixel API.

        Must be called once before :meth:`get_progress` or
        :meth:`find_collection_by_name`.
        """
        raw: dict[str, Any] = await self.client.get_collections_resource()
        self._definitions = {}
        self._item_id_to_name = {}

        for category_id, category_data in raw.get("collections", {}).items():
            for item_id, item_data in category_data.get("items", {}).items():
                tiers: list[dict[str, int]] = []
                for t in item_data.get("tiers", []):
                    tiers.append(
                        {"tier": t["tier"], "amountRequired": t["amountRequired"]}
                    )

                self._definitions[item_id] = {
                    "name": item_data.get("name", item_id),
                    "category": category_id.lower(),
                    "max_tier": item_data.get("maxTiers", len(tiers)),
                    "tiers": sorted(tiers, key=lambda x: x["tier"]),
                }
                self._item_id_to_name[item_id] = item_data.get("name", item_id)

        logger.info(
            "Loaded %d collection definitions across categories",
            len(self._definitions),
        )

    def get_progress(
        self,
        player_collections: dict[str, int],
        collection_filter: str | None = None,
        target_tier: int | None = None,
    ) -> list[CollectionProgress]:
        """Compute collection progress for a player.

        Parameters
        ----------
        player_collections:
            Mapping of collection item ID → amount collected.
        collection_filter:
            Optional name or ID to restrict results to a single
            collection.
        target_tier:
            Optional specific tier to track progress toward.

        Returns
        -------
        list[CollectionProgress]
            Sorted by *remaining* ascending (closest-to-completion first).

        Raises
        ------
        RuntimeError
            If :meth:`load_definitions` has not been called.
        """
        if not self._definitions:
            raise RuntimeError(
                "Collection definitions not loaded. Call load_definitions() first."
            )

        results: list[CollectionProgress] = []

        for item_id, defn in self._definitions.items():
            # Apply optional filter
            if collection_filter:
                if (
                    collection_filter.upper() != item_id
                    and collection_filter.lower() != defn["name"].lower()
                ):
                    continue

            current_amount = player_collections.get(item_id, 0)

            # Determine current tier
            current_tier = 0
            for t in defn["tiers"]:
                if current_amount >= t["amountRequired"]:
                    current_tier = t["tier"]
                else:
                    break

            max_tier: int = defn["max_tier"]

            # Determine the effective next tier
            if target_tier is not None:
                effective_next = min(target_tier, max_tier)
            else:
                effective_next = min(current_tier + 1, max_tier)

            # Find the requirement for the next tier
            next_req = 0
            for t in defn["tiers"]:
                if t["tier"] == effective_next:
                    next_req = t["amountRequired"]
                    break

            remaining = max(0, next_req - current_amount)

            # Calculate percentage progress toward the next tier
            if next_req > 0:
                current_tier_req = 0
                for t in defn["tiers"]:
                    if t["tier"] == current_tier:
                        current_tier_req = t["amountRequired"]

                tier_range = next_req - current_tier_req
                if tier_range > 0:
                    progress_pct = min(
                        100.0,
                        (current_amount - current_tier_req) / tier_range * 100,
                    )
                else:
                    progress_pct = 100.0
            else:
                progress_pct = 100.0 if current_tier >= max_tier else 0.0

            results.append(
                CollectionProgress(
                    name=defn["name"],
                    item_id=item_id,
                    category=defn["category"],
                    current_amount=current_amount,
                    current_tier=current_tier,
                    max_tier=max_tier,
                    next_tier=effective_next,
                    next_tier_req=next_req,
                    remaining=remaining,
                    progress_pct=round(progress_pct, 1),
                )
            )

        # Sort by items remaining (closest to completion first)
        results.sort(key=lambda p: p.remaining)
        return results

    def find_collection_by_name(self, query: str) -> str | None:
        """Fuzzy-search for a collection ID from user input.

        Tries exact ID match, then exact name match, then partial
        substring match.

        Parameters
        ----------
        query:
            User-supplied search string.

        Returns
        -------
        str | None
            The matching item ID, or ``None`` if no match is found.
        """
        if not self._definitions:
            return None

        # Exact ID match
        if query.upper() in self._definitions:
            return query.upper()

        # Exact name match (case-insensitive)
        for item_id, defn in self._definitions.items():
            if defn["name"].lower() == query.lower():
                return item_id

        # Partial / substring match
        for item_id, defn in self._definitions.items():
            if query.lower() in defn["name"].lower() or query.lower() in item_id.lower():
                return item_id

        return None
