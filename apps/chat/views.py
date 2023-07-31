from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import (PrivateChatSerializer, PrivateMessageSerializer)
from .models import PrivateChat, PrivateMessage 



class PrivateChatViewSet(viewsets.ViewSet):
    serializer_class = PrivateChatSerializer

    @swagger_auto_schema(
        operation_summary='Все чаты',
        operation_description='Получить список всех чатов'
        )
    @action(detail=False, methods=['get'])
    def get_chats(self, request):
        return Response(PrivateChatSerializer(PrivateChat.objects.all()).data)
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user1': openapi.Schema(type=openapi.TYPE_INTEGER),
            'user2': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['user1', 'user2']),
        operation_summary='Создать чат',
        operation_description="""
        Эндпоинт для создания чата, необходимо передать id пользователей"""
    )
    @action(detail=False, methods=['post'])
    def create_chat(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class PrivateMessageViewSet(viewsets.ViewSet):
    serializer_class = PrivateMessageSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение всех сообщений в приватном чате", 
        operation_summary="Получение сообщений")
    @action(detail=False, methods=['get'], url_path='messages/(?P<private_chat_id>\d+)')
    def list_messages(self, request, private_chat_id=None, *args, **kwargs):
        """
        Получение всех сообщений в приватном чате.
        """
        queryset = PrivateMessage.objects.filter(private_chat_id=private_chat_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['content']),
        operation_description="Отправка сообщения в приватный чат",
        operation_summary="Отправка сообщения")
    @action(detail=False, methods=['post'], url_path='send/(?P<private_chat_id>\d+)')
    def send_message(self, request, private_chat_id=None, *args, **kwargs):
        """
        Отправка сообщения в приватный чат.
        """
        private_chat = PrivateChat.objects.get(id=private_chat_id)
        user1_id = private_chat.user1_id
        user2_id = private_chat.user2_id
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        data = request.data.copy() # Create mutable copy
        data['private_chat_id'] = private_chat_id
        data['sender'] = request.user.id
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        private_message = serializer.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'private_chat_{user1_id}_{user2_id}', 
            {
                'type': 'chat_message',
                'message': serializer.data
            }
        )
        return Response(serializer.data)





