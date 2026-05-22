from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import Organization
from campaigns.models import Campaign
from buyers.models import Buyer, BuyerCampaign
from routing.models import CallLog
from .models import RTBAuction, RTBBid
from .services import RTBService


class RTBServiceDuplicateTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.campaign = Campaign.objects.create(
            organization=self.org,
            name='Test Campaign',
            bid_floor=Decimal('5.00'),
        )
        self.buyer = Buyer.objects.create(
            organization=self.org,
            name='Test Buyer',
            status='active',
            rtb_endpoint='https://buyer.example.com/rtb',
            dup_window_days=30,
        )
        BuyerCampaign.objects.create(
            campaign=self.campaign,
            buyer=self.buyer,
            is_active=True,
        )

    def test_no_duplicate_when_no_calls(self):
        result = RTBService.is_duplicate_for_buyer(self.buyer, '+15551234567')
        self.assertFalse(result)

    def test_duplicate_detected_within_window(self):
        CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            buyer=self.buyer,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_dup_1',
        )
        result = RTBService.is_duplicate_for_buyer(self.buyer, '+15551234567')
        self.assertTrue(result)

    def test_duplicate_not_detected_outside_window(self):
        old_call = CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            buyer=self.buyer,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_dup_2',
        )
        old_call.created_at = timezone.now() - timedelta(days=31)
        old_call.save()
        result = RTBService.is_duplicate_for_buyer(self.buyer, '+15551234567')
        self.assertFalse(result)

    def test_zero_window_disables_dup_check(self):
        self.buyer.dup_window_days = 0
        self.buyer.save()
        CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            buyer=self.buyer,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_dup_3',
        )
        result = RTBService.is_duplicate_for_buyer(self.buyer, '+15551234567')
        self.assertFalse(result)

    def test_eligible_buyers_excludes_duplicates(self):
        CallLog.objects.create(
            organization=self.org,
            campaign=self.campaign,
            buyer=self.buyer,
            caller_number='+15551234567',
            called_number='+15559999999',
            twilio_call_sid='CA_elig_1',
        )
        eligible = RTBService.get_eligible_buyers(self.campaign, '+15551234567')
        self.assertEqual(len(eligible), 0)

    def test_eligible_buyers_includes_fresh_caller(self):
        eligible = RTBService.get_eligible_buyers(self.campaign, '+15559876543')
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0].id, self.buyer.id)

    def test_inactive_buyer_excluded(self):
        self.buyer.status = 'inactive'
        self.buyer.save()
        eligible = RTBService.get_eligible_buyers(self.campaign, '+15559876543')
        self.assertEqual(len(eligible), 0)

    def test_buyer_without_rtb_endpoint_excluded(self):
        self.buyer.rtb_endpoint = ''
        self.buyer.save()
        eligible = RTBService.get_eligible_buyers(self.campaign, '+15559876543')
        self.assertEqual(len(eligible), 0)