from django.urls import path
from .views import PrivateChatView, PrivateMessageView

urlpatterns = [
    path('private_chat/', PrivateChatView.as_view(), name='private_chat'),
    path('private_message/<int:private_chat_id>/', PrivateMessageView.as_view(), name='private_message'),
]
