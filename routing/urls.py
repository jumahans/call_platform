from django.urls import path
from . import twilio_handler
from call_queue import views as queue_views

urlpatterns = [
    path('incoming-call/', twilio_handler.incoming_call, name='incoming_call'),
    path('call-status/', twilio_handler.call_status, name='call_status'),
    path('whisper/<str:campaign_id>/', twilio_handler.whisper, name='whisper'),
    path('queue-wait/<str:campaign_id>/', queue_views.queue_wait, name='queue_wait'),
]