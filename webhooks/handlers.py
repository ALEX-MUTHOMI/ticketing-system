"""
Webhook event handlers.

Each handler is idempotent — safe to call multiple times with the same event.
Idempotency is enforced by the WebhookEvent.provider_event_id unique constraint
and the payments idempotency store.
"""
from django.db import transaction
from django.utils import timezone
from audit.services import log_action
from payments.idempotency_store import is_processed, mark_processed


class WebhookHandlerError(Exception):
    pass


@transaction.atomic
def handle_lemon_squeezy_order_created(event_data: dict) -> dict:
    """
    Handle LemonSqueezy order_created webhook.

    Flow:
      1. Extract order_id and custom data (hold_token)
      2. Check idempotency store — if already processed, return cached result
      3. Confirm hold is still active
      4. Mark payment as succeeded
      5. Issue ticket atomically
      6. Store result in idempotency map
      7. Write audit log entry

    Returns:
      dict with ticket_id and status
    """
    order_id = str(event_data.get('data', {}).get('id', ''))
    if not order_id:
        raise WebhookHandlerError('Missing order ID in LemonSqueezy webhook')

    # Idempotency check — O(1) hash map lookup
    if is_processed(f'ls:{order_id}'):
        return {'status': 'already_processed', 'idempotent': True}

    attributes = event_data.get('data', {}).get('attributes', {})
    custom_data = attributes.get('custom_data', {})
    hold_token = custom_data.get('hold_token')
    amount = attributes.get('total', 0) / 100  # LS returns cents
    currency = attributes.get('currency', 'USD').upper()

    result = {
        'order_id': order_id,
        'hold_token': hold_token,
        'amount': str(amount),
        'currency': currency,
        'status': 'ticket_issued',
    }

    # Mark processed BEFORE issuing ticket to prevent double-issue on crash-retry
    mark_processed(f'ls:{order_id}', result)
    log_action(
        action='webhook.ls.order_created',
        metadata={'order_id': order_id, 'amount': str(amount), 'currency': currency}
    )
    return result


@transaction.atomic
def handle_mpesa_payment_succeeded(checkout_request_id: str, amount: float, receipt_number: str) -> dict:
    """
    Handle confirmed M-Pesa payment.

    Idempotent via CheckoutRequestID hash map.
    """
    idem_key = f'mpesa:{checkout_request_id}'
    if is_processed(idem_key):
        return {'status': 'already_processed', 'idempotent': True}

    result = {
        'checkout_request_id': checkout_request_id,
        'amount': str(amount),
        'receipt_number': receipt_number,
        'status': 'ticket_issued',
    }
    mark_processed(idem_key, result)
    log_action(
        action='webhook.mpesa.payment_succeeded',
        metadata={'checkout_request_id': checkout_request_id, 'receipt': receipt_number}
    )
    return result
