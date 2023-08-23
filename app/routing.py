from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('wss/updates/', consumers.UpdateConsumer.as_asgi()),
]
