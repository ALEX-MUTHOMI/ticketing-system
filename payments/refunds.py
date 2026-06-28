"""
Refund services.

Security:
  - Refund guard: ticket cannot be refunded after check-in (Attack 6)
  - Atomic: payment status + inventory restoration in single transaction
  - Audit log on every refund action
"""
from django.db import transaction
from .models import Payment, PaymentStatus
from audit.services import log_action


class RefundError(Exception):
    pass


class PostCheckinRefundError(RefundError):
    """Raised when attempting to refund a ticket that has already been checked in."""
    pass


@transaction.atomic
def request_refund(payment_id: str, reason: str, actor=None) -> dict:
    """
    Process a refund request.

    Security check: Reject if any ticket in this payment is already checked in.
    This prevents the attack: use ticket then claim refund.

    Args:
        payment_id: UUID of the Payment to refund.
        reason: Refund reason from the requestor.
        actor: User requesting the refund.

    Returns:
        dict with refund status and amount.

    Raises:
        PostCheckinRefundError: If ticket already checked in.
        RefundError: On any other refund failure.
    """
    payment = Payment.objects.select_for_update().get(id=payment_id)

    if payment.status != PaymentStatus.SUCCEEDED:
        raise RefundError(f'Cannot refund payment with status: {payment.status}')

    # Attack 6 guard: reject if any associated ticket is already checked in
    from tickets.models import Ticket, TicketStatus
    checked_in_tickets = Ticket.objects.filter(
        payment=payment,
        status=TicketStatus.CHECKED_IN
    ).count()

    if checked_in_tickets > 0:
        raise PostCheckinRefundError(
            f'Cannot refund: {checked_in_tickets} ticket(s) already checked in.'
        )

    # Mark payment as refunded
    payment.status = PaymentStatus.REFUNDED
    payment.save(update_fields=['status'])

    # Restore inventory for all tickets in this payment
    from inventory.models import TicketTier
    for ticket in Ticket.objects.filter(payment=payment):
        TicketTier.objects.filter(id=ticket.tier_id).update(
            quantity_sold=ticket.tier.quantity_sold - 1
        )
        ticket.status = TicketStatus.CANCELLED
        ticket.save(update_fields=['status'])

    log_action(
        action='payment.refunded',
        actor=actor,
        entity=payment,
        metadata={'reason': reason, 'amount': str(payment.amount)}
    )

    return {
        'status': 'refunded',
        'payment_id': str(payment_id),
        'amount': str(payment.amount),
        'currency': payment.currency,
    }
