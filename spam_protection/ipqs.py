"""IPQualityScore phone number validation."""
import requests
from django.conf import settings


class IPQSService:
    """Wrapper for IPQualityScore phone number API."""

    BASE_URL = "https://www.ipqualityscore.com/api/json/phone"

    @classmethod
    def check_phone(cls, phone_number: str, country: str = "US") -> dict:
        """Check a phone number with IPQS. Returns the full JSON response."""
        api_key = getattr(settings, 'IPQS_API_KEY', '')
        if not api_key:
            return {"success": False, "error": "IPQS_API_KEY not configured"}

        clean_number = phone_number.lstrip('+').strip()
        url = f"{cls.BASE_URL}/{api_key}/{clean_number}"

        try:
            r = requests.get(url, params={"country[]": country}, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def should_block(cls, ipqs_result: dict, campaign) -> tuple:
        """Decide if a call should be blocked. Returns (should_block, reason)."""
        if not ipqs_result.get('success', True):
            return False, ""

        if getattr(campaign, 'block_voip', False) and ipqs_result.get('VOIP', False):
            return True, "voip_blocked"

        if getattr(campaign, 'block_risky', False) and ipqs_result.get('risky', False):
            return True, "risky_caller"

        if getattr(campaign, 'block_spammer', False) and ipqs_result.get('spammer', False):
            return True, "known_spammer"

        if getattr(campaign, 'block_recent_abuse', False) and ipqs_result.get('recent_abuse', False):
            return True, "recent_abuse"

        max_fraud_score = getattr(campaign, 'max_fraud_score', 100)
        fraud_score = ipqs_result.get('fraud_score', 0)
        if fraud_score > max_fraud_score:
            return True, f"fraud_score_too_high"

        if getattr(campaign, 'block_invalid_numbers', False) and not ipqs_result.get('valid', True):
            return True, "invalid_number"

        return False, ""