import asyncio
import time
import httpx
from decimal import Decimal
from django.utils import timezone
from .models import RTBAuction, RTBBid


# How long we wait for buyer bids in seconds
BID_TIMEOUT = 5


class RTBEngine:

    @staticmethod
    async def ping_buyer(
        buyer,
        auction: RTBAuction,
        ping_payload: dict,
    ) -> dict:
        """
        Ping a single buyer endpoint with the auction details.
        Returns the bid response or a timeout/error result.
        """
        start = time.monotonic()

        try:
            timeout = ping_payload.get('_timeout', BID_TIMEOUT)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    buyer.rtb_endpoint,
                    json=ping_payload,
                    headers={'Content-Type': 'application/json'},
                )

            elapsed_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                return {
                    'buyer'      : buyer,
                    'bid_amount' : Decimal(str(data.get('bid_amount', 0))),
                    'accept'     : data.get('accept', True),
                    'raw'        : data,
                    'status'     : RTBBid.Status.PENDING,
                    'response_ms': elapsed_ms,
                }

            # Buyer returned non-200 — treat as no bid
            return {
                'buyer'      : buyer,
                'bid_amount' : None,
                'accept'     : False,
                'raw'        : {},
                'status'     : RTBBid.Status.REJECTED,
                'response_ms': elapsed_ms,
            }

        except (httpx.TimeoutException, asyncio.TimeoutError):
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return {
                'buyer'      : buyer,
                'bid_amount' : None,
                'accept'     : False,
                'raw'        : {},
                'status'     : RTBBid.Status.TIMEOUT,
                'response_ms': elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return {
                'buyer'      : buyer,
                'bid_amount' : None,
                'accept'     : False,
                'raw'        : {'error': str(e)},
                'status'     : RTBBid.Status.REJECTED,
                'response_ms': elapsed_ms,
            }

    @staticmethod
    async def run_auction(auction: RTBAuction, buyers: list) -> RTBAuction:
        """
        Ping all buyers in parallel, collect bids, pick the winner.
        Saves all bids and updates the auction in the database.
        """
        start = time.monotonic()

        timeout = auction.campaign.rtb_timeout_seconds or BID_TIMEOUT

        # Derive area code from caller number (don't leak full number to losing bidders)
        cleaned = auction.caller_number.replace('+1', '').replace('+', '')
        caller_area_code = cleaned[:3] if len(cleaned) >= 3 else ''

        ping_payload = {
            'auction_id'      : str(auction.id),
            'campaign_id'     : str(auction.campaign_id),
            'caller_area_code': caller_area_code,
            'caller_state'    : auction.caller_state,
            'call_time'       : timezone.now().isoformat(),
            'bid_floor'       : str(auction.campaign.bid_floor or 0),
            'timeout_ms'      : timeout * 1000,
            '_timeout'        : timeout,
        }
        # Ping all buyers at the same time
        tasks = [
            RTBEngine.ping_buyer(buyer, auction, ping_payload)
            for buyer in buyers
        ]
        results = await asyncio.gather(*tasks)

        duration_ms = int((time.monotonic() - start) * 1000)

        # Save all bids
        bids = []
        for result in results:
            bid = await asyncio.to_thread(
                RTBBid.objects.create,
                auction=auction,
                buyer=result['buyer'],
                bid_amount=result['bid_amount'],
                status=result['status'],
                response_ms=result['response_ms'],
                raw_response=result['raw'],
            )
            bids.append((bid, result))

        # Find the winner — highest bid from a buyer who accepted
        bid_floor = auction.campaign.bid_floor or Decimal('0')
        valid_bids = [
            (bid, result)
            for bid, result in bids
            if result['accept']
            and result['bid_amount']
            and result['bid_amount'] >= bid_floor
            and result['bid_amount'] > 0
        ]

        if not valid_bids:
            auction.status     = RTBAuction.Status.NO_BIDS
            auction.duration_ms = duration_ms
            await asyncio.to_thread(auction.save)
            return auction

        # Sort by bid amount descending, pick top
        valid_bids.sort(key=lambda x: x[1]['bid_amount'], reverse=True)
        winning_bid_obj, winning_result = valid_bids[0]

        # Mark winner
        winning_bid_obj.status = RTBBid.Status.WON
        await asyncio.to_thread(winning_bid_obj.save)

        # Mark losers
        for bid, _ in valid_bids[1:]:
            bid.status = RTBBid.Status.LOST
            await asyncio.to_thread(bid.save)

        # Update auction
        auction.status      = RTBAuction.Status.CLOSED
        auction.winning_bid = winning_result['bid_amount']
        auction.winner      = winning_result['buyer']
        auction.duration_ms = duration_ms
        await asyncio.to_thread(auction.save)

        return auction

    @staticmethod
    def start_auction(campaign, caller_number: str, caller_state: str, twilio_call_sid: str = '') -> RTBAuction:
        """
        Synchronous entry point called by the routing engine.
        Creates the auction, fetches eligible RTB buyers, runs the async auction.
        """
        from rtb.services import RTBService

        auction = RTBAuction.objects.create(
            organization_id=campaign.organization_id,
            campaign=campaign,
            caller_number=caller_number,
            caller_state=caller_state,
            twilio_call_sid=twilio_call_sid,
            status=RTBAuction.Status.OPEN,
        )

        # Get eligible buyers (filters out duplicates, caps, concurrency)
        buyers = RTBService.get_eligible_buyers(campaign, caller_number)

        if not buyers:
            auction.status = RTBAuction.Status.NO_BIDS
            auction.save()
            return auction

        # Run the async auction from sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already inside an async context (e.g. ASGI)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, RTBEngine.run_auction(auction, buyers))
                    future.result()
            else:
                loop.run_until_complete(RTBEngine.run_auction(auction, buyers))
        except Exception:
            auction.status = RTBAuction.Status.TIMEOUT
            auction.save()

        auction.refresh_from_db()
        return auction