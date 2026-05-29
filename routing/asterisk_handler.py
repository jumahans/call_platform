import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone

from phone_numbers.models import PhoneNumber
from routing.models import CallLog
from routing.engine import RoutingEngine


def _check_secret(request):
    secret = request.headers.get('X-Asterisk-Secret', '')
    expected = getattr(settings, 'ASTERISK_SHARED_SECRET', '')
    return secret and expected and secret == expected


@csrf_exempt
@require_http_methods(["POST"])
def route_incoming_call(request):
    """Asterisk calls this when a call comes in. Returns the buyer to dial."""
    if not _check_secret(request):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Bad JSON"}, status=400)

    caller = data.get('caller_number', '')
    called = data.get('called_number', '')
    asterisk_call_id = data.get('asterisk_call_id', '')

    if not caller or not called:
        return JsonResponse({"error": "Missing fields"}, status=400)

    try:
        phone = PhoneNumber.objects.select_related('campaign').get(
            number=called, is_active=True
        )
    except PhoneNumber.DoesNotExist:
        return JsonResponse({"action": "hangup", "reason": "number_not_found"})

    campaign = phone.campaign
    if not campaign or campaign.status != 'active':
        return JsonResponse({"action": "hangup", "reason": "campaign_inactive"})

    call_log = CallLog.objects.create(
        organization=campaign.organization,
        campaign=campaign,
        phone_number=phone,
        caller_number=caller,
        called_number=called,
        twilio_call_sid=asterisk_call_id,
        status='ringing',
        started_at=timezone.now(),
    )

    decision = RoutingEngine.route_call(campaign, caller, call_log)

    if not decision or not decision.get('buyer'):
        call_log.status = 'no_buyer'
        call_log.ended_at = timezone.now()
        call_log.save()
        return JsonResponse({"action": "hangup", "reason": "no_buyer"})

    buyer = decision['buyer']
    call_log.buyer = buyer
    call_log.save()

    return JsonResponse({
        "action": "dial",
        "buyer_number": buyer.phone_number,
        "call_log_id": str(call_log.id),
        "max_duration": 3600,
    })


@csrf_exempt
@require_http_methods(["POST"])
def call_ended(request):
    """Asterisk calls this when the call ends. Logs duration + status."""
    if not _check_secret(request):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Bad JSON"}, status=400)

    call_log_id = data.get('call_log_id', '')
    duration = int(data.get('duration', 0))
    answered = bool(data.get('answered', False))
    recording_url = data.get('recording_url', '')

    if not call_log_id:
        return JsonResponse({"error": "Missing call_log_id"}, status=400)

    try:
        call_log = CallLog.objects.get(id=call_log_id)
    except CallLog.DoesNotExist:
        return JsonResponse({"error": "Call not found"}, status=404)

    call_log.duration_seconds = duration
    call_log.status = 'completed' if answered else 'no_answer'
    call_log.ended_at = timezone.now()
    if recording_url:
        call_log.recording_url = recording_url
    call_log.save()

    return JsonResponse({"received": True, "call_log_id": str(call_log.id)})