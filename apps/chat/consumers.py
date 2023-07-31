from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from .models import PrivateMessage, PrivateChat
import json

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id_1 = self.scope['url_route']['kwargs']['user_id_1']
        self.user_id_2 = self.scope['url_route']['kwargs']['user_id_2']

        self.room_group_name = f'private_chat_{self.user_id_1}_{self.user_id_2}'

        # Join chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()  # Accept the connection before sending any messages

        # Send the chat history
        messages = await self.get_chat_history()
        for message in messages:
            await self.send(text_data=json.dumps({
                'content': message['content'],
                'sender': message['sender'],
                'timestamp': message['timestamp'].isoformat()
            }))

    async def disconnect(self, close_code):
        # Leave chat room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to chat room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def get_chat_history(self):
        # Find the chat where both users are participants
        chat = PrivateChat.objects.filter(
            Q(user1_id=self.user_id_1, user2_id=self.user_id_2) |
            Q(user1_id=self.user_id_2, user2_id=self.user_id_1)
        ).distinct()

        if not chat.exists():
            return []

        # Get the messages of the chat
        messages = PrivateMessage.objects.filter(
            private_chat=chat.first()
        ).order_by('timestamp').values('content', 'sender', 'timestamp')

        return list(messages)
