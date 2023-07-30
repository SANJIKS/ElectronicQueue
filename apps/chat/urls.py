from django.urls import path
from .views import ChatGroupView, MessageView, PrivateChatView, PrivateMessageView

urlpatterns = [
    path('chat_group/', ChatGroupView.as_view(), name='chat_group'),
    path('message/<int:chat_group_id>/', MessageView.as_view(), name='message'),
    path('private_chat/', PrivateChatView.as_view(), name='private_chat'),
    path('private_message/<int:private_chat_id>/', PrivateMessageView.as_view(), name='private_message'),
]
