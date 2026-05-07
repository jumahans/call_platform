import uuid
from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import RTBAuction, RTBBid
from .schemas import RTBAuctionOutSchema, BidResponseSchema, MessageSchema

router = Router(tags=['RTB'])


# ─── Auctions ─────────────────────────────────────────────────────────────────

@router.get('/auctions', response=List[RTBAuctionOutSchema])
def list_auctions(
    request,
    campaign_id : uuid.UUID = None,
    status      : str       = None,
    limit       : int       = 100,
):
    """List all RTB auctions for the organisation."""
    qs = RTBAuction.objects.filter(
        organization_id=request.auth.organization_id
    ).prefetch_related('bids')

    if campaign_id:
        qs = qs.filter(campaign_id=campaign_id)
    if status:
        qs = qs.filter(status=status)

    return qs.order_by('-created_at')[:limit]


@router.get('/auctions/{auction_id}', response=RTBAuctionOutSchema)
def get_auction(request, auction_id: uuid.UUID):
    """Get a single auction with all bids."""
    auction = get_object_or_404(
        RTBAuction,
        id=auction_id,
        organization_id=request.auth.organization_id
    )
    return auction


# ─── Buyer Bid Endpoint ───────────────────────────────────────────────────────

@router.post('/bid', response={200: MessageSchema, 400: MessageSchema}, auth=None)
def submit_bid(request, payload: BidResponseSchema):
    """
    Buyers POST their bid to this endpoint when they receive a ping.
    Auth is None — buyers authenticate via auction_id which is a secret UUID.
    """
    try:
        auction = RTBAuction.objects.get(
            id=payload.auction_id,
            status=RTBAuction.Status.OPEN
        )
    except RTBAuction.DoesNotExist:
        return 400, {'message': 'Auction not found or already closed'}

    updated = RTBBid.objects.filter(
        auction=auction,
        status=RTBBid.Status.PENDING,
    ).update(
        bid_amount=payload.bid_amount,
        raw_response={'bid_amount': str(payload.bid_amount), 'accept': payload.accept},
    )

    if not updated:
        return 400, {'message': 'No pending bid found for this auction'}

    return 200, {'message': 'Bid received'}


# ─── Bids ─────────────────────────────────────────────────────────────────────

@router.get('/auctions/{auction_id}/bids', response=List[dict])
def list_bids(request, auction_id: uuid.UUID):
    """List all bids for a specific auction."""
    auction = get_object_or_404(
        RTBAuction,
        id=auction_id,
        organization_id=request.auth.organization_id
    )
    return list(
        auction.bids.values(
            'id', 'buyer_id', 'bid_amount',
            'status', 'response_ms', 'created_at'
        )
    )