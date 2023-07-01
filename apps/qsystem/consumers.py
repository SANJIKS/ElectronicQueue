import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

User = get_user_model()

from .models import Customer
class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Принимаем соединение
        await self.accept()

        # Добавляем текущий канал в группу "ticket_broadcast"
        await self.channel_layer.group_add("ticket_broadcast", self.channel_name)

    async def disconnect(self, close_code):
        # Удаляем текущий канал из группы "ticket_broadcast"
        await self.channel_layer.group_discard("ticket_broadcast", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        if action == 'create_ticket':
            await self.create_ticket(text_data_json)

    @database_sync_to_async
    def create_ticket(self, data):
        user_id = data['user_id']
        
        # Получение пользователя
        user = User.objects.get(id=user_id)

        # Создание талона
        ticket = Customer.objects.create(user=user)

        # Получение данных талона
        ticket_data = {
            'id': ticket.id,
            'user_id': ticket.user.id,
            'ticket_number': ticket.ticket_number,
            'position': ticket.position,
            'created_at': ticket.created_at.isoformat(),
            # Другие поля талона
        }

        self.send_ticket_data(ticket_data)

    async def send_ticket_data(self, ticket_data):
        # Отправка данных талона клиенту
        await self.send(text_data=json.dumps({
            'action': 'ticket_created',
            'ticket_data': ticket_data
        }))






