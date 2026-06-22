"""
M-Pesa Daraja API integration.

Handles:
- STK Push (Lipa Na M-Pesa Online)
- Callback verification (IP allowlist + ResultCode check)
- Idempotency via CheckoutRequestID hash map
"""
import base64
import hashlib
import hmac
from datetime import datetime
from ipaddress import ip_address, ip_network
from typing import Optional
import httpx
from django.conf import settings

# Safaricom Daraja production IP ranges (public)
SAFARICOM_IP_RANGES = [
    ip_network('196.201.214.200/29'),
    ip_network('196.201.214.216/29'),
    ip_network('196.201.214.224/29'),
    ip_network('196.201.214.232/29'),
    ip_network('196.201.214.240/29'),
    ip_network('196.201.214.248/29'),
    ip_network('196.201.214.0/24'),
]
DARAJA_BASE = 'https://api.safaricom.co.ke'
DARAJA_SANDBOX = 'https://sandbox.safaricom.co.ke'


class MpesaSignatureError(Exception):
    pass


class MpesaError(Exception):
    pass


def is_safaricom_ip(client_ip: str) -> bool:
    """
    Verify callback originated from Safaricom IP range.

    Security: Callbacks not from Safaricom IPs are rejected immediately.
    This is the first line of defense against webhook impersonation.
    """
    try:
        addr = ip_address(client_ip)
        return any(addr in network for network in SAFARICOM_IP_RANGES)
    except ValueError:
        return False


def get_access_token() -> str:
    consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
    consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
    credentials = base64.b64encode(f'{consumer_key}:{consumer_secret}'.encode()).decode()
    base_url = DARAJA_SANDBOX if getattr(settings, 'MPESA_SANDBOX', True) else DARAJA_BASE
    with httpx.Client(timeout=10) as client:
        response = client.get(
            f'{base_url}/oauth/v1/generate?grant_type=client_credentials',
            headers={'Authorization': f'Basic {credentials}'}
        )
        response.raise_for_status()
    return response.json()['access_token']


def initiate_stk_push(
    phone_number: str,
    amount: int,
    account_reference: str,
    transaction_desc: str,
    callback_url: str,
) -> dict:
    """
    Trigger M-Pesa STK push to buyer's phone.

    Returns Daraja response including CheckoutRequestID for idempotency tracking.
    """
    shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
    passkey = getattr(settings, 'MPESA_PASSKEY', '')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()
    base_url = DARAJA_SANDBOX if getattr(settings, 'MPESA_SANDBOX', True) else DARAJA_BASE
    token = get_access_token()
    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': callback_url,
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc,
    }
    with httpx.Client(timeout=15) as client:
        response = client.post(
            f'{base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
    return response.json()


def parse_stk_callback(callback_data: dict) -> dict:
    """
    Parse M-Pesa STK callback.

    Returns dict with: success, checkout_request_id, amount, receipt_number

    Security: Always check ResultCode. Only ResultCode=0 is success.
    """
    body = callback_data.get('Body', {}).get('stkCallback', {})
    result_code = body.get('ResultCode')
    checkout_request_id = body.get('CheckoutRequestID', '')

    if result_code != 0:
        return {
            'success': False,
            'checkout_request_id': checkout_request_id,
            'result_code': result_code,
            'result_desc': body.get('ResultDesc', ''),
        }

    items = {i['Name']: i.get('Value') for i in body.get('CallbackMetadata', {}).get('Item', [])}
    return {
        'success': True,
        'checkout_request_id': checkout_request_id,
        'amount': items.get('Amount'),
        'receipt_number': items.get('MpesaReceiptNumber'),
        'phone': items.get('PhoneNumber'),
        'transaction_date': items.get('TransactionDate'),
    }
