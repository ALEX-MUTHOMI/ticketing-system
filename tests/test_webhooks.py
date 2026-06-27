import pytest
from unittest.mock import patch
from webhooks.handlers import handle_lemon_squeezy_order_created, handle_mpesa_payment_succeeded


class TestLemonSqueezyHandler:
    def test_valid_order_processed(self):
        event = {
            'data': {
                'id': 'order-123',
                'attributes': {
                    'total': 150000,
                    'currency': 'USD',
                    'custom_data': {'hold_token': 'hold-abc'},
                }
            }
        }
        with patch('webhooks.handlers.is_processed', return_value=False), \
             patch('webhooks.handlers.mark_processed'), \
             patch('webhooks.handlers.log_action'):
            result = handle_lemon_squeezy_order_created(event)
        assert result['status'] == 'ticket_issued'
        assert result['order_id'] == 'order-123'

    def test_duplicate_order_returns_idempotent_response(self):
        """Attack 3: Payment replay — second delivery silently returns cached result."""
        event = {'data': {'id': 'order-123', 'attributes': {'total': 150000, 'currency': 'USD', 'custom_data': {}}}}
        with patch('webhooks.handlers.is_processed', return_value=True):
            result = handle_lemon_squeezy_order_created(event)
        assert result['idempotent'] is True
        assert result['status'] == 'already_processed'


class TestMpesaHandler:
    def test_valid_mpesa_payment_processed(self):
        with patch('webhooks.handlers.is_processed', return_value=False), \
             patch('webhooks.handlers.mark_processed'), \
             patch('webhooks.handlers.log_action'):
            result = handle_mpesa_payment_succeeded('ws_CO_123', 1500.0, 'NLJ7RT61SV')
        assert result['status'] == 'ticket_issued'
        assert result['receipt_number'] == 'NLJ7RT61SV'

    def test_mpesa_replay_blocked(self):
        """Second M-Pesa callback with same CheckoutRequestID is idempotent."""
        with patch('webhooks.handlers.is_processed', return_value=True):
            result = handle_mpesa_payment_succeeded('ws_CO_123', 1500.0, 'NLJ7RT61SV')
        assert result['idempotent'] is True
