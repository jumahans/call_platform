from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.request_validator import RequestValidator
from django.conf import settings
from .models import CallLog, RoutingRule
from .engine import RoutingEngine
from phone_numbers.models import PhoneNumber


def validate_twilio_request(request: HttpRequest) -> bool:
    """Validate that the request is genuinely from Twilio"""
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    signature = request.headers.get('X-Twilio-Signature', '')
    url = request.build_absolute_uri()
    post_data = request.POST.dict()
    return validator.validate(url, post_data, signature)


@csrf_exempt
def incoming_call(request: HttpRequest) -> HttpResponse:
    """Handle incoming call from Twilio"""

    if request.method != 'POST':
        return HttpResponse(status=405)

    # Validate request is from Twilio
    # Uncomment in production:
    # if not validate_twilio_request(request):
    #     return HttpResponse(status=403)

    # Extract call data from Twilio
    call_sid = request.POST.get('CallSid', '')
    caller_number = request.POST.get('From', '')
    called_number = request.POST.get('To', '')
    caller_state = request.POST.get('FromState', '')
    caller_country = request.POST.get('FromCountry', '')

    # Get area code from caller number
    caller_area_code = ''
    if caller_number and len(caller_number) >= 5:
        cleaned = caller_number.replace('+1', '').replace('+', '')
        caller_area_code = cleaned[:3]

    if not caller_state and caller_area_code:
        caller_state = RoutingEngine.get_caller_state(caller_area_code)

    response = VoiceResponse()

    try:
        # Find which phone number was called
        phone_number = PhoneNumber.objects.select_related(
            'campaign', 'publisher'
        ).get(number=called_number, status='active')

        if not phone_number.campaign:
            response.say("This number is not configured. Please try again later.")
            response.hangup()
            return HttpResponse(str(response), content_type='text/xml')

        campaign = phone_number.campaign

        # Build call data for routing engine
        call_data = {
            'caller_number': caller_number,
            'caller_area_code': caller_area_code,
            'caller_state': caller_state,
            'caller_country': caller_country,
            'call_time': timezone.now(),
            'tags': [],
        }

        # Route the call
        routing_result = RoutingEngine.route_call(str(campaign.id), call_data)

        # Create call log
        call_log = CallLog.objects.create(
            organization=campaign.organization,
            campaign=campaign,
            routing_rule=routing_result.get('rule'),
            buyer=routing_result.get('buyer'),
            publisher=phone_number.publisher,
            caller_number=caller_number,
            called_number=called_number,
            twilio_call_sid=call_sid,
            status=CallLog.Status.RINGING,
            caller_area_code=caller_area_code,
            caller_state=caller_state,
            caller_country=caller_country,
            buyer_payout=campaign.payout_amount,
            revenue=campaign.revenue_amount,
            publisher_payout=phone_number.publisher.payout_amount if phone_number.publisher else 0,
        )

        destination = routing_result.get('destination')

        if destination:
            call_log.destination_number = destination
            call_log.save(update_fields=['destination_number'])

            dial = Dial(
                action=f"{settings.BASE_URL}/api/twilio/call-status/",
                method='POST',
                timeout=30,
                record='record-from-answer',
            )
            dial.number(destination)
            response.append(dial)
        else:
            response.say("We are sorry, no agents are available right now. Please try again later.")
            response.hangup()

            call_log.status = CallLog.Status.NO_ANSWER
            call_log.save(update_fields=['status'])

    except PhoneNumber.DoesNotExist:
        response.say("This number is not recognized. Please try again later.")
        response.hangup()

    except Exception as e:
        response.say("We are experiencing technical difficulties. Please try again later.")
        response.hangup()

    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
def call_status(request: HttpRequest) -> HttpResponse:
    """Handle call status updates from Twilio"""

    if request.method != 'POST':
        return HttpResponse(status=405)

    call_sid = request.POST.get('CallSid', '')
    call_status = request.POST.get('CallStatus', '')
    call_duration = request.POST.get('CallDuration', 0)
    recording_url = request.POST.get('RecordingUrl', '')
    recording_sid = request.POST.get('RecordingSid', '')

    status_map = {
        'completed': CallLog.Status.COMPLETED,
        'no-answer': CallLog.Status.NO_ANSWER,
        'busy': CallLog.Status.BUSY,
        'failed': CallLog.Status.FAILED,
        'in-progress': CallLog.Status.IN_PROGRESS,
    }

    try:
        call_log = CallLog.objects.get(twilio_call_sid=call_sid)

        call_log.status = status_map.get(call_status, CallLog.Status.FAILED)
        call_log.duration = int(call_duration) if call_duration else 0
        call_log.ended_at = timezone.now()

        if recording_url:
            call_log.recording_url = recording_url
            call_log.recording_sid = recording_sid

        call_log.save()

    except CallLog.DoesNotExist:
        pass

    return HttpResponse('', content_type='text/xml')