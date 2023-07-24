from django.urls import re_path

from apps.qsystem.consumers import TicketConsumer, ScoreBoardConsumer, CabinetConsumer

websocket_urlpatterns = [
    re_path(r'ws/customers/(?P<userId>\w+)/$', TicketConsumer.as_asgi()),
    re_path(r'ws/board/(?P<branch_id>\w+)/$', ScoreBoardConsumer.as_asgi()),
    re_path(r'ws/waitlist/(?P<branch_id>\w+)/$', CabinetConsumer.as_asgi())
]