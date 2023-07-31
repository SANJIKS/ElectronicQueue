from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .serializers import (PrivateChatSerializer, PrivateMessageSerializer)
from .models import PrivateChat, PrivateMessage 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class PrivateChatView(generics.CreateAPIView):
    serializer_class = PrivateChatSerializer

    @swagger_auto_schema(operation_description="Создание приватного чата", operation_summary="Создание приватного чата")
    def create(self, request, *args, **kwargs):
        """
        Создание нового приватного чата.
        """
        return super().create(request, *args, **kwargs)


class PrivateMessageView(generics.ListCreateAPIView):
    serializer_class = PrivateMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        private_chat_id = self.kwargs.get('private_chat_id')
        return PrivateMessage.objects.filter(private_chat_id=private_chat_id)

    @swagger_auto_schema(operation_description="Получение всех сообщений в приватном чате", operation_summary="Получение сообщений")
    def list(self, request, *args, **kwargs):
        """
        Получение всех сообщений в приватном чате.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Отправка сообщения в приватный чат", operation_summary="Отправка сообщения")
    def perform_create(self, serializer):
        """
        Отправка сообщения в приватный чат.
        """
        private_chat_id = self.kwargs.get('private_chat_id')
        private_chat = PrivateChat.objects.get(id=private_chat_id)
        
        user1_id = private_chat.user1_id
        user2_id = private_chat.user2_id

        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        private_message = serializer.save(sender=self.request.user, private_chat_id=private_chat_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'private_chat_{user1_id}_{user2_id}', 
            {
                'type': 'chat_message',
                'message': self.serializer_class(private_message).data
            }
        )