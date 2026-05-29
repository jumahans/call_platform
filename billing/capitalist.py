"""Capitalist.net merchant payment integration."""
import hashlib
from decimal import Decimal
from django.conf import settings


class CapitalistService:
    """Wrapper for Capitalist.net merchant payment form.

    Capitalist doesn't have a 'create order via API' endpoint for shops.
    Instead, you redirect the user to their payment form with signed
    parameters. They handle the checkout and POST status updates to
    your Status URL.
    """

    CHECKOUT_URL = 'https://capitalist.net/merchants/pay'

    @classmethod
    def build_checkout(cls, amount: Decimal, currency: str, order_id: str,
                       description: str = ''):
        """Build the checkout URL parameters to send the user to Capitalist."""
        merchant_id = getattr(settings, 'CAPITALIST_MERCHANT_ID', '')
        secret = getattr(settings, 'CAPITALIST_SECRET', '')

        amount_str = f'{Decimal(amount):.2f}'
        # Capitalist signature: md5(merchant_id + order_id + amount + currency + secret)
        sig_raw = f'{merchant_id}{order_id}{amount_str}{currency.upper()}{secret}'
        signature = hashlib.md5(sig_raw.encode('utf-8')).hexdigest()

        params = {
            'merchant_id': merchant_id,
            'order_id': str(order_id),
            'amount': amount_str,
            'currency': currency.upper(),
            'description': description or f'Deposit {amount_str} {currency.upper()}',
            'signature': signature,
        }

        query = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'{cls.CHECKOUT_URL}?{query}', params

    @classmethod
    def verify_callback(cls, data: dict) -> bool:
        """Verify the signature on a callback from Capitalist."""
        merchant_id = getattr(settings, 'CAPITALIST_MERCHANT_ID', '')
        secret = getattr(settings, 'CAPITALIST_SECRET', '')

        received_sig = data.get('signature', '')
        order_id = data.get('order_id', '')
        amount = data.get('amount', '')
        currency = data.get('currency', '')
        status = data.get('status', '')

        sig_raw = f'{merchant_id}{order_id}{amount}{currency}{status}{secret}'
        expected_sig = hashlib.md5(sig_raw.encode('utf-8')).hexdigest()

        return received_sig.lower() == expected_sig.lower()