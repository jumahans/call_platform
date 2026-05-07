from django.urls import path
from . import twilio_handler

urlpatterns = [
    path('incoming-call/', twilio_handler.incoming_call, name='incoming_call'),
    path('call-status/', twilio_handler.call_status, name='call_status'),
]