import pytest
from unittest.mock import patch, MagicMock
from payments.refunds import request_refund, PostCheckinRefundError, RefundError


class TestRefundGuard:
    def test_refund_rejected_if_ticket_checked_in(self):
        """Attack 6: Use ticket then claim refund — blocked."""
        with patch('payments.refunds.Payment.objects') as mock_payment_obj, \
             patch('payments.refunds.Ticket.objects') as mock_ticket_obj:
            mock_payment = MagicMock()
            mock_payment.status = 'succeeded'
            mock_payment_obj.select_for_update.return_value.get.return_value = mock_payment
            mock_ticket_obj.filter.return_value.count.return_value = 1  # 1 checked-in ticket
            with pytest.raises(PostCheckinRefundError):
                request_refund('payment-id', reason='Changed mind')

    def test_refund_rejected_for_non_succeeded_payment(self):
        with patch('payments.refunds.Payment.objects') as mock_payment_obj:
            mock_payment = MagicMock()
            mock_payment.status = 'pending'
            mock_payment_obj.select_for_update.return_value.get.return_value = mock_payment
            with pytest.raises(RefundError, match='Cannot refund payment with status'):
                request_refund('payment-id', reason='Test')

    def test_valid_refund_succeeds(self):
        with patch('payments.refunds.Payment.objects') as mock_payment_obj, \
             patch('payments.refunds.Ticket.objects') as mock_ticket_obj, \
             patch('payments.refunds.log_action'):
            mock_payment = MagicMock()
            mock_payment.status = 'succeeded'
            mock_payment.amount = '1500.00'
            mock_payment.currency = 'KES'
            mock_payment_obj.select_for_update.return_value.get.return_value = mock_payment
            mock_ticket_obj.filter.return_value.count.return_value = 0  # Not checked in
            mock_ticket_obj.filter.return_value.__iter__ = lambda s: iter([])
            result = request_refund('payment-id', reason='Event cancelled')
        assert result['status'] == 'refunded'
