from django.urls import re_path

from apps.qsystem.consumers import TicketConsumer, ScoreBoardConsumer, CabinetConsumer
from apps.chat.consumers import PrivateChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/customers/(?P<userId>\w+)/$', TicketConsumer.as_asgi()),
    re_path(r'ws/waitlist/(?P<branch_id>\w+)/$', CabinetConsumer.as_asgi()),
    re_path(r'ws/board/(?P<branch_id>\w+)/$', ScoreBoardConsumer.as_asgi()),
    re_path(r'ws/private_chat/(?P<user_id_1>\d+)/(?P<user_id_2>\d+)/$', PrivateChatConsumer.as_asgi()),
]
