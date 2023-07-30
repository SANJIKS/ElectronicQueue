from django.urls import re_path

from apps.qsystem.consumers import TicketConsumer, ScoreBoardConsumer, CabinetConsumer
from apps.chat.consumers import GroupChatConsumer, PrivateChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/customers/(?P<userId>\w+)/$', TicketConsumer.as_asgi()),
    re_path(r'ws/board/(?P<branch_id>\w+)/$', ScoreBoardConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<chat_group_id>\d+)/$', GroupChatConsumer.as_asgi()),
    re_path(r'ws/private_chat/(?P<private_chat_id>\d+)/$', PrivateChatConsumer.as_asgi()),
]