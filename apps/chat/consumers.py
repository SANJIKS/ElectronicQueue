from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatGroup, Message, PrivateMessage, PrivateChat
import json
from asgiref.sync import sync_to_async

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chat_group_id']
        self.room_group_name = f'chat_group_{self.room_name}'

        # Join chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send chat history
        messages = await self.get_chat_history(self.room_name)
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message.content,
                'sender': message.sender.username,
                'timestamp': str(message.timestamp)
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

    @sync_to_async
    def get_chat_history(self, chat_group_id):
        chat_group = ChatGroup.objects.get(id=chat_group_id)
        return list(Message.objects.select_related('sender').filter(chat_group=chat_group).order_by('timestamp'))



class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['private_chat_id']
        self.room_group_name = f'private_chat_{self.room_name}'

        # Join chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Send the chat history
        messages = await self.get_chat_history()
        for message in messages:
            await self.send(text_data=json.dumps({
                'content': message['content'],
                'sender': message['sender'],
                'timestamp': message['timestamp'].isoformat()
            }))

        await self.accept()

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
        messages = PrivateMessage.objects.filter(
            private_chat_id=self.room_name
        ).order_by('timestamp').values('content', 'sender__username', 'timestamp')
        return list(messages)