import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from accounts.consumers import ActivityConsumer
from routing.consumers import LiveCallConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/activity/", ActivityConsumer.as_asgi()),
            path("ws/live-calls/", LiveCallConsumer.as_asgi()),
        ])
    ),
})