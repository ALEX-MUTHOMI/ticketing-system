"""
Binary search tier selector for O(log N) budget-based tier selection.

Problem: Given a list of ticket tiers sorted by price, find the best
available tier that fits within a given budget.

Naive approach: Linear scan O(N) — iterate all tiers until we find one.
Optimised approach: Binary search O(log N) — tiers are already sorted by
price (enforced by Meta.ordering), so we bisect to the target.

For typical event sizes (2-10 tiers) the difference is negligible, but
for platform-wide tier queries across hundreds of events it matters.
"""
import bisect
from decimal import Decimal
from typing import Optional


class TierSelector:
    """
    Selects the best available tier for a given budget using binary search.

    Time complexity: O(log N) for selection after O(N) build.
    The build (sort) is done once per request, not per tier.
    """

    def __init__(self, tiers):
        """
        Args:
            tiers: QuerySet or list of TicketTier objects sorted by price.
        """
        self._tiers = list(tiers)
        self._prices = [float(t.price) for t in self._tiers]

    def select_for_budget(self, budget: Decimal) -> Optional[object]:
        """
        Find the highest-priced available tier within budget.
        Uses bisect_right to find insertion point, then walks left.

        Args:
            budget: Maximum price the buyer will pay.

        Returns:
            Best TicketTier or None if no available tier within budget.

        Time complexity: O(log N) binary search + O(K) walk-left where
        K is the number of unavailable tiers near the budget boundary.
        """
        budget_float = float(budget)
        # bisect_right gives us the insertion point after all equal prices
        idx = bisect.bisect_right(self._prices, budget_float) - 1

        # Walk left to find first available tier within budget
        while idx >= 0:
            tier = self._tiers[idx]
            if tier.quantity_available > 0 and tier.is_on_sale():
                return tier
            idx -= 1

        return None

    def select_exact(self, price: Decimal) -> Optional[object]:
        """Find a tier at an exact price. O(log N)."""
        price_float = float(price)
        idx = bisect.bisect_left(self._prices, price_float)
        if idx < len(self._prices) and self._prices[idx] == price_float:
            return self._tiers[idx]
        return None
