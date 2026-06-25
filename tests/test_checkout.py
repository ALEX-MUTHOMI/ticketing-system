import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from checkout.services import HoldAbuseError, InsufficientInventoryError

User = get_user_model()


class TestHoldCreation:
    @pytest.mark.django_db
    def test_hold_abuse_guard_blocks_third_hold(self):
        """Attack 2: User cannot create more than MAX holds per event."""
        from checkout.services import MAX_HOLDS_PER_USER_PER_EVENT
        with patch('checkout.services.CheckoutHold.objects') as mock_objects:
            mock_objects.filter.return_value.count.return_value = MAX_HOLDS_PER_USER_PER_EVENT
            tier = MagicMock()
            tier.quantity_available = 10
            mock_objects.select_for_update.return_value.get.return_value = tier
            with pytest.raises(HoldAbuseError):
                from checkout.services import create_hold
                user = MagicMock()
                create_hold(user, 'tier-id', 1)

    def test_insufficient_inventory_raises(self):
        """Attack 4: Race condition — zero inventory blocks hold."""
        with patch('checkout.services.TicketTier.objects') as mock_tier_objects, \
             patch('checkout.services.CheckoutHold.objects') as mock_hold_objects:
            tier = MagicMock()
            tier.quantity_available = 0
            mock_tier_objects.select_for_update.return_value.get.return_value = tier
            mock_hold_objects.filter.return_value.count.return_value = 0
            with pytest.raises(InsufficientInventoryError):
                from checkout.services import create_hold
                user = MagicMock()
                create_hold(user, 'tier-id', 1)
