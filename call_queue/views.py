from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .services import CallQueueService
from campaigns.models import Campaign


@csrf_exempt
def queue_wait(request: HttpRequest, campaign_id: str) -> HttpResponse:
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        twiml = CallQueueService.get_wait_twiml(campaign)
    except Campaign.DoesNotExist:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response><Play loop="5">https://com.twilio.music.classical.s3.amazonaws.com/BusyStrings.mp3</Play></Response>'''

    return HttpResponse(twiml, content_type='text/xml')