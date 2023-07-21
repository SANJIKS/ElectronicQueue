import json
from datetime import date

from asgiref.sync import async_to_sync, sync_to_async
# from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.generic.websocket import (AsyncWebsocketConsumer,
                                        WebsocketConsumer)

from .models import Branch, Customer

# User = get_user_model()




class TicketConsumer(AsyncWebsocketConsumer):
    def getUser(self, userId):
        from django.contrib.auth import get_user_model
        User = get_user_model()
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
        return Customer.objects.filter(created_at__date=date.today(), is_served=None, queue__operator=self.user,old_operator=None, operator=None).order_by('position')

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



class ScoreBoardConsumer(AsyncWebsocketConsumer):
    def getBranch(self, branch_id):
        return Branch.objects.get(id=branch_id)
    
    async def connect(self):
        self.branch_id = self.scope['url_route']['kwargs']['branch_id']
        self.branch = await database_sync_to_async(self.getBranch)(self.branch_id)

        await self.accept()

        await self.channel_layer.group_add(f"score_broadcast", self.channel_name)
        await self.send_ticket_list('ahaha')

    async def get_ticket_list(self):
        tickets = await sync_to_async(self.get_tickets)()

        ticket_list = []

        async for ticket in tickets:
            ticket_data = {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'status': 'started' if ticket.operator_id else 'called',
                'created_at': ticket.created_at.isoformat(),
            }
            ticket_list.append(ticket_data)

        return ticket_list
    
    def get_tickets(self):
        return Customer.objects.filter(
            created_at__date=date.today(), 
            is_served=None, 
            queue__branch=self.branch_id
        ).exclude(number_of_calls=0)

    async def send_ticket_list(self, event=None):
        ticket_list = await self.get_ticket_list()
        await self.send(text_data=json.dumps({
            'action': 'ticket_list_updated',
            'ticket_data': ticket_list
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"score_boardcas", self.channel_name)
    
    # async def send_group_ticket_list(self, ticket_list):
    #     await self.channel_layer.group_send(
    #         f"ticket_status_updates_{self.branch_id}",
    #         {
    #             'type': 'ticket_list_updated',
    #             'ticket_list': ticket_list,
    #         }
    #     )

    # async def ticket_list_updated(self, event):
    #     ticket_list = event['ticket_list']
    #     await self.send(text_data=json.dumps(ticket_list))

    # @database_sync_to_async
    # def get_branch(self, branch_id):
    #     try:
    #         return Branch.objects.get(pk=branch_id)
    #     except Branch.DoesNotExist:
    #         return None
        

    # async def receive(self, text_data):
    #     ticket_list = await self.get_ticket_list()

    #     await self.send_group_ticket_list(ticket_list)