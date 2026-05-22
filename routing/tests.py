from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import Organization, User
from campaigns.models import Campaign
from buyers.models import Buyer
from .models import RoutingRule, RuleDestination, CallLog
from .engine import RoutingEngine


class DuplicateDetectionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.campaign = Campaign.objects.create(
            organization=self.org,
            name='Test Campaign',
            duplicate_call_block=True,
            duplicate_call_block_hours=24,
        )

    def test_no_duplicate_when_no_calls(self):
        result = RoutingEngine.is_duplicate('+15551234567', str(self.campaign.id), 24)
        self.assertFalse(result)

    def test_duplicate_detected_within_window(self):
        CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_test_1',
        )
        result = RoutingEngine.is_duplicate('+15551234567', str(self.campaign.id), 24)
        self.assertTrue(result)

    def test_duplicate_not_detected_outside_window(self):
        old_call = CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_test_2',
        )
        old_call.created_at = timezone.now() - timedelta(hours=48)
        old_call.save()
        result = RoutingEngine.is_duplicate('+15551234567', str(self.campaign.id), 24)
        self.assertFalse(result)

    def test_zero_block_hours_disables_dup_check(self):
        CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_test_3',
        )
        result = RoutingEngine.is_duplicate('+15551234567', str(self.campaign.id), 0)
        self.assertFalse(result)


class CallerStateLookupTests(TestCase):
    def test_known_area_code_returns_state(self):
        self.assertEqual(RoutingEngine.get_caller_state('212'), 'NY')
        self.assertEqual(RoutingEngine.get_caller_state('310'), 'CA')
        self.assertEqual(RoutingEngine.get_caller_state('305'), 'FL')

    def test_unknown_area_code_returns_unknown(self):
        self.assertEqual(RoutingEngine.get_caller_state('000'), 'Unknown')