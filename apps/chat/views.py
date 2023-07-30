from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from .serializers import (ChatGroupSerializer, MessageSerializer, 
                          PrivateChatSerializer, PrivateMessageSerializer)
from .models import Message, PrivateMessage 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ChatGroupView(generics.CreateAPIView):
    serializer_class = ChatGroupSerializer

    @swagger_auto_schema(operation_description="Создание группового чата", operation_summary="Создание группового чата")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class MessageView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_group_id = self.kwargs.get('chat_group_id')
        return Message.objects.filter(chat_group_id=chat_group_id)

    @swagger_auto_schema(operation_description="Получение всех сообщений в групповом чате", operation_summary="Получение сообщений")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Отправка сообщения в групповой чат", operation_summary="Отправка сообщения")
    def perform_create(self, serializer):
        chat_group_id = self.kwargs.get('chat_group_id')
        message = serializer.save(sender=self.request.user, chat_group_id=chat_group_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_group_{message.chat_group.id}', 
            {
                'type': 'chat_message',
                'message': self.serializer_class(message).data
            }
        )


class PrivateChatView(generics.CreateAPIView):
    serializer_class = PrivateChatSerializer

    @swagger_auto_schema(operation_description="Создание приватного чата", operation_summary="Создание приватного чата")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class PrivateMessageView(generics.ListCreateAPIView):
    serializer_class = PrivateMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        private_chat_id = self.kwargs.get('private_chat_id')
        return PrivateMessage.objects.filter(private_chat_id=private_chat_id)

    @swagger_auto_schema(operation_description="Получение всех сообщений в приватном чате", operation_summary="Получение сообщений")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Отправка сообщения в приватный чат", operation_summary="Отправка сообщения")
    def perform_create(self, serializer):
        private_chat_id = self.kwargs.get('private_chat_id')
        private_message = serializer.save(sender=self.request.user, private_chat_id=private_chat_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'private_chat_{private_message.private_chat.id}', 
            {
                'type': 'chat_message',
                'message': self.serializer_class(private_message).data
            }
        )
