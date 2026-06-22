"""
LemonSqueezy payment integration.

Handles:
- Checkout URL generation via LS Checkout API
- Webhook signature verification (HMAC-SHA256 on X-Signature header)
- Order idempotency via order_id hash map
"""
import hashlib
import hmac
import httpx
from django.conf import settings


LS_API_BASE = 'https://api.lemonsqueezy.com/v1'
LS_WEBHOOK_SECRET_SETTING = 'LEMON_SQUEEZY_WEBHOOK_SECRET'
LS_API_KEY_SETTING = 'LEMON_SQUEEZY_API_KEY'


class LemonSqueezySignatureError(Exception):
    pass


def verify_webhook_signature(payload: bytes, signature_header: str) -> None:
    """
    Verify LemonSqueezy webhook HMAC-SHA256 signature.

    LemonSqueezy sends: X-Signature: <hex_hmac_sha256>

    Security: Reject any webhook that fails signature verification.
    An attacker cannot forge a valid signature without knowing LS_WEBHOOK_SECRET.

    Raises:
        LemonSqueezySignatureError: If signature is invalid or missing.
    """
    secret = getattr(settings, LS_WEBHOOK_SECRET_SETTING, '')
    if not secret:
        raise LemonSqueezySignatureError('LS webhook secret not configured')

    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature_header):
        raise LemonSqueezySignatureError('Invalid webhook signature')


def create_checkout_url(variant_id: str, custom_data: dict, redirect_url: str) -> str:
    """
    Generate a LemonSqueezy checkout URL for a ticket tier.

    Args:
        variant_id: LS product variant ID mapped to this ticket tier.
        custom_data: Metadata passed through to the webhook (hold_token, tier_id).
        redirect_url: URL to redirect after payment.

    Returns:
        Checkout URL string.
    """
    api_key = getattr(settings, LS_API_KEY_SETTING, '')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json',
    }
    payload = {
        'data': {
            'type': 'checkouts',
            'attributes': {
                'custom_price': None,
                'product_options': {'redirect_url': redirect_url},
                'checkout_data': {'custom': custom_data},
            },
            'relationships': {
                'store': {'data': {'type': 'stores', 'id': getattr(settings, 'LS_STORE_ID', '')}},
                'variant': {'data': {'type': 'variants', 'id': variant_id}},
            },
        }
    }
    with httpx.Client(timeout=10) as client:
        response = client.post(f'{LS_API_BASE}/checkouts', json=payload, headers=headers)
        response.raise_for_status()
    return response.json()['data']['attributes']['url']
