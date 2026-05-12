from ninja import Router, Query
from django.http import HttpRequest, HttpResponse
from typing import List

from accounts.api import JWTAuth
from .schemas import (
    AnalyticsFilterSchema,
    DashboardSchema,
    TimeSeriesPointSchema,
    CampaignPerformanceSchema,
    BuyerPerformanceSchema,
    PublisherPerformanceSchema,
    CallLogListSchema,
)
from .services import AnalyticsService

router = Router(tags=["Analytics"], auth=JWTAuth())


@router.get("/dashboard", response={200: DashboardSchema})
def dashboard(request: HttpRequest):
    """Real-time dashboard — total calls, live calls, revenue, conversion rate."""
    data = AnalyticsService.get_dashboard(request.auth)
    return 200, data


@router.get("/time-series", response={200: List[TimeSeriesPointSchema]})
def time_series(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Calls/revenue/profit over time. granularity: hour | day | week | month"""
    data = AnalyticsService.get_time_series(request.auth, filters)
    return 200, data


@router.get("/campaigns", response={200: List[CampaignPerformanceSchema]})
def campaign_performance(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Performance breakdown per campaign."""
    data = AnalyticsService.get_campaign_performance(request.auth, filters)
    return 200, data


@router.get("/buyers", response={200: List[BuyerPerformanceSchema]})
def buyer_performance(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Performance breakdown per buyer — win rate, avg bid, payout."""
    data = AnalyticsService.get_buyer_performance(request.auth, filters)
    return 200, data


@router.get("/publishers", response={200: List[PublisherPerformanceSchema]})
def publisher_performance(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Performance breakdown per publisher — calls, conversion, spam rate."""
    data = AnalyticsService.get_publisher_performance(request.auth, filters)
    return 200, data


@router.get("/calls", response={200: CallLogListSchema})
def call_log(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Full paginated call log with all filters."""
    data = AnalyticsService.get_call_log(request.auth, filters)
    return 200, data


@router.get("/calls/export", auth=JWTAuth(), response=None)
def export_calls(request: HttpRequest, filters: AnalyticsFilterSchema = Query(...)):
    """Download full call log as CSV."""
    csv_data = AnalyticsService.export_csv(request.auth, filters)
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="call_log.csv"'
    return response