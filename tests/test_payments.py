import pytest
from unittest.mock import patch
from payments.mpesa import is_safaricom_ip, parse_stk_callback


class TestMpesaCallback:
    def test_successful_callback_parsed(self):
        callback = {
            'Body': {
                'stkCallback': {
                    'ResultCode': 0,
                    'CheckoutRequestID': 'ws_CO_123',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 1500},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'NLJ7RT61SV'},
                            {'Name': 'PhoneNumber', 'Value': 254712345678},
                            {'Name': 'TransactionDate', 'Value': 20260620095807},
                        ]
                    }
                }
            }
        }
        result = parse_stk_callback(callback)
        assert result['success'] is True
        assert result['checkout_request_id'] == 'ws_CO_123'
        assert result['amount'] == 1500
        assert result['receipt_number'] == 'NLJ7RT61SV'

    def test_failed_callback_parsed(self):
        callback = {
            'Body': {
                'stkCallback': {
                    'ResultCode': 1032,
                    'CheckoutRequestID': 'ws_CO_456',
                    'ResultDesc': 'Request cancelled by user',
                }
            }
        }
        result = parse_stk_callback(callback)
        assert result['success'] is False
        assert result['result_code'] == 1032

    def test_non_safaricom_ip_rejected(self):
        assert is_safaricom_ip('8.8.8.8') is False
        assert is_safaricom_ip('196.201.214.201') is True
