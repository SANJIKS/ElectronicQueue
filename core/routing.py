from django.urls import re_path

from apps.qsystem.consumers import TicketConsumer

websocket_urlpatterns = [
    re_path(r'ws/customers/(?P<userId>\w+)/$', TicketConsumer.as_asgi()),
]