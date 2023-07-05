import json
from datetime import date
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

User = get_user_model()

from .models import Customer


from asgiref.sync import sync_to_async

class TicketConsumer(AsyncWebsocketConsumer):
    def getUser(self, userId):
        return User.objects.get(id=userId)

    async def connect(self):
        self.userId = self.scope['url_route']['kwargs']['userId']
        self.user = await database_sync_to_async(self.getUser)(self.userId)

        await self.accept()
        await self.channel_layer.group_add("ticket_broadcast", self.channel_name)
        await self.send_ticket_list('ahahah')

    async def get_ticket_list(self):
        tickets = await database_sync_to_async(self.get_tickets)()
        
        ticket_list = []
        
        async for ticket in tickets:
            ticket_data = {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'position': ticket.position,
                'created_at': ticket.created_at.isoformat(),
            }
            ticket_list.append(ticket_data)

        return ticket_list


    def get_tickets(self):
        return Customer.objects.filter(created_at__date=date.today(), is_served=None, queue__operator=self.user)

    async def send_ticket_list(self, event):
        ticket_list = await self.get_ticket_list()
        await self.send(text_data=json.dumps({
            'action': 'ticket_list_updated',
            'ticket_data': ticket_list
        }))



    async def disconnect(self, close_code):
        # Удаляем текущий канал из группы "ticket_broadcast"
        await self.channel_layer.group_discard("ticket_broadcast", self.channel_name)


    # async def receive(self, text_data):
    #     text_data_json = json.loads(text_data)
    #     action = text_data_json['action']
        # if action == 'create_ticket':
        #     await self.create_ticket(text_data_json)
        
        # await self.send_ticket_list()