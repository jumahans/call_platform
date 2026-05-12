# save as test_rtb.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from campaigns.models import Campaign
from rtb.engine import RTBEngine

campaign = Campaign.objects.get(id='2417ab91-bb73-45f9-8f64-07210eaa1dfa')

auction = RTBEngine.start_auction(
    campaign=campaign,
    caller_number='+254700392123',
    caller_state='FL',
    twilio_call_sid='TEST123'
)

print(f"Auction ID: {auction.id}")
print(f"Auction Status: {auction.status}")
print(f"Winner: {auction.winner}")
print(f"Winning Bid: {auction.winning_bid}")
print(f"Duration: {auction.duration_ms}ms")