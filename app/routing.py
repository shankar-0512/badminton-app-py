from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/updates/', consumers.UpdateConsumer.as_asgi()),
]
