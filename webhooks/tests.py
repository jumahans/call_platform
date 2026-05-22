from decimal import Decimal
from django.test import TestCase
from accounts.models import Organization
from .models import ConversionPixel, ConversionEvent
from .services import ConversionPixelService


class ConversionPixelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')


    def test_record_conversion_with_invalid_token(self):
        result = ConversionPixelService.record_conversion(
            token='invalid-token',
            caller_number='+15551234567',
        )
        self.assertFalse(result['success'])
        self.assertIn('Invalid', result['error'])

    def test_record_conversion_with_valid_token(self):
        pixel = ConversionPixel.objects.create(
            organization=self.org,
            name='Test Pixel',
            token='valid-token-123',
            conversion_value=Decimal('25.00'),
        )

        result = ConversionPixelService.record_conversion(
            token='valid-token-123',
            caller_number='+15551234567',
            conversion_value=Decimal('50.00'),
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['conversion_value'], '50.00')

        # Verify event was created
        self.assertEqual(ConversionEvent.objects.count(), 1)
        event = ConversionEvent.objects.first()
        self.assertEqual(event.caller_number, '+15551234567')
        self.assertEqual(event.conversion_value, Decimal('50.00'))

    def test_record_conversion_uses_pixel_default_value(self):
        pixel = ConversionPixel.objects.create(
            organization=self.org,
            name='Test Pixel',
            token='token-456',
            conversion_value=Decimal('30.00'),
        )

        result = ConversionPixelService.record_conversion(
            token='token-456',
            caller_number='+15559998888',
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['conversion_value'], '30.00')

    def test_inactive_pixel_rejects_conversion(self):
        pixel = ConversionPixel.objects.create(
            organization=self.org,
            name='Test Pixel',
            token='paused-token',
            status=ConversionPixel.Status.PAUSED,
        )

        result = ConversionPixelService.record_conversion(
            token='paused-token',
            caller_number='+15551234567',
        )

        self.assertFalse(result['success'])