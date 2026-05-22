from datetime import timedelta
from django.utils import timezone
from .models import RTBAuction, RTBBid


class RTBService:
    """Business logic for RTB auctions — buyer eligibility, dup checks, fraud detection."""

    @staticmethod
    def is_duplicate_for_buyer(buyer, caller_number: str) -> bool:
        """
        Check if this caller has already been sent to this buyer within the dup window.
        Returns True if duplicate (buyer should be excluded from auction).
        """
        from routing.models import CallLog

        if buyer.dup_window_days <= 0:
            return False

        cutoff = timezone.now() - timedelta(days=buyer.dup_window_days)

        return CallLog.objects.filter(
            buyer=buyer,
            caller_number=caller_number,
            created_at__gte=cutoff,
        ).exists()

    @staticmethod
    def get_eligible_buyers(campaign, caller_number: str):
        """
        Return buyers eligible for this auction.
        Filters out: inactive buyers, buyers at concurrency cap,
        buyers at daily/monthly cap, buyers in dup window.
        """
        from buyers.models import Buyer
        from routing.engine import RoutingEngine

        buyers = Buyer.objects.filter(
            campaign_buyers__campaign=campaign,
            campaign_buyers__is_active=True,
            status='active',
            rtb_endpoint__isnull=False,
        ).exclude(rtb_endpoint='')

        eligible = []
        for buyer in buyers:
            # Skip if duplicate caller for this buyer
            if RTBService.is_duplicate_for_buyer(buyer, caller_number):
                continue

            # Skip if buyer at daily/monthly cap
            if not RoutingEngine.check_buyer_caps(buyer):
                continue

            # Skip if buyer at concurrency cap
            if not RoutingEngine.check_buyer_concurrency(buyer):
                continue

            eligible.append(buyer)

        return eligible
    @staticmethod
    def update_buyer_quality_score(buyer):
        """
        Recalculate buyer quality score based on recent call outcomes.
        Score range: 0-100. Based on last 100 calls.
        """
        from datetime import timedelta
        from django.utils import timezone
        from routing.models import CallLog

        recent_calls = CallLog.objects.filter(
            buyer=buyer,
            created_at__gte=timezone.now() - timedelta(days=30),
        ).order_by('-created_at')[:100]

        total = recent_calls.count()
        if total == 0:
            return buyer.quality_score

        completed = sum(1 for c in recent_calls if c.status == CallLog.Status.COMPLETED)
        long_calls = sum(1 for c in recent_calls if c.duration >= 60)
        failed = sum(1 for c in recent_calls if c.status in (CallLog.Status.FAILED, CallLog.Status.NO_ANSWER, CallLog.Status.BUSY))

        completion_rate = (completed / total) * 50      # max 50 points
        engagement_rate = (long_calls / total) * 30     # max 30 points
        reliability = max(0, 20 - (failed / total) * 20)  # max 20 points

        score = int(completion_rate + engagement_rate + reliability)
        score = max(0, min(100, score))

        buyer.quality_score = score
        buyer.quality_score_updated_at = timezone.now()
        buyer.save(update_fields=['quality_score', 'quality_score_updated_at'])

        return score