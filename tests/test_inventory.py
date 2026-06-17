import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from inventory.tier_selector import TierSelector


def make_tier(price, available=10, on_sale=True):
    t = MagicMock()
    t.price = Decimal(str(price))
    t.quantity_available = available
    t.is_on_sale.return_value = on_sale
    return t


class TestTierSelector:
    def test_select_exact_budget_match(self):
        tiers = [make_tier(500), make_tier(1000), make_tier(2000)]
        selector = TierSelector(tiers)
        result = selector.select_for_budget(Decimal('1000'))
        assert float(result.price) == 1000

    def test_select_best_tier_within_budget(self):
        tiers = [make_tier(500), make_tier(1000), make_tier(2000)]
        selector = TierSelector(tiers)
        result = selector.select_for_budget(Decimal('1500'))
        assert float(result.price) == 1000

    def test_returns_none_if_no_tier_within_budget(self):
        tiers = [make_tier(1000), make_tier(2000)]
        selector = TierSelector(tiers)
        result = selector.select_for_budget(Decimal('500'))
        assert result is None

    def test_skips_sold_out_tiers(self):
        tiers = [make_tier(500), make_tier(1000, available=0), make_tier(2000)]
        selector = TierSelector(tiers)
        result = selector.select_for_budget(Decimal('1000'))
        assert float(result.price) == 500

    def test_skips_tiers_not_on_sale(self):
        tiers = [make_tier(500), make_tier(1000, on_sale=False)]
        selector = TierSelector(tiers)
        result = selector.select_for_budget(Decimal('1000'))
        assert float(result.price) == 500

    def test_select_exact_price(self):
        tiers = [make_tier(500), make_tier(1000)]
        selector = TierSelector(tiers)
        result = selector.select_exact(Decimal('500'))
        assert float(result.price) == 500

    def test_select_exact_returns_none_for_missing_price(self):
        tiers = [make_tier(500), make_tier(1000)]
        selector = TierSelector(tiers)
        result = selector.select_exact(Decimal('750'))
        assert result is None
