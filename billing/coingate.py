"""CoinGate crypto payment integration."""
import requests
from decimal import Decimal
from django.conf import settings


class CoinGateService:
    """Wrapper around CoinGate REST API for crypto deposits."""

    @staticmethod
    def _base_url():
        env = getattr(settings, 'COINGATE_ENVIRONMENT', 'sandbox')
        if env == 'live':
            return 'https://api.coingate.com/api/v2'
        return 'https://api-sandbox.coingate.com/api/v2'

    @staticmethod
    def _headers():
        api_key = getattr(settings, 'COINGATE_API_KEY', '')
        return {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

    @classmethod
    def create_order(cls, amount: Decimal, currency: str, order_id: str,
                     callback_url: str, success_url: str, cancel_url: str,
                     title: str = 'Account Deposit', description: str = ''):
        """Create a CoinGate checkout order. Returns dict with payment_url."""
        payload = {
            'order_id': str(order_id),
            'price_amount': str(amount),
            'price_currency': currency.upper(),
            'receive_currency': 'DO_NOT_CONVERT',
            'title': title,
            'description': description or f'Deposit of {amount} {currency}',
            'callback_url': callback_url,
            'success_url': success_url,
            'cancel_url': cancel_url,
        }
        r = requests.post(
            f'{cls._base_url()}/orders',
            json=payload,
            headers=cls._headers(),
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    @classmethod
    def get_order(cls, coingate_order_id: str):
        """Fetch an order's current status from CoinGate."""
        r = requests.get(
            f'{cls._base_url()}/orders/{coingate_order_id}',
            headers=cls._headers(),
            timeout=15,
        )
        r.raise_for_status()
        return r.json()