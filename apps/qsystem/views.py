from datetime import datetime, timedelta, time, date
from pytz import timezone as timez

from django.urls import reverse
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField, Count
from decouple import config
from django.db.models import Max
from django.utils.text import slugify

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .permissions import IsOperator, IsOperatorOfCustomer, IsAdmin


from .models import Queue, Customer, Waiting_List
from .serializers import GetQueueCustomersSerializer, QueueSerializer, CustomerSerializer, ShiftWindow, WaitingListSerializer
from apps.branches.models import Window, Calendar


class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    permission_classes = [IsAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)
    

    @action(detail=True, methods=['get'])
    def get_documents(self, request, pk=None):
        queue = Queue.objects.get(pk=pk)

        documents = {
            'Обязательные документы':queue.documents,
            'Необязательные документы': queue.optional_documents
        }
        return Response(documents, status=200)



class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        if self.action == 'change_status' or self.action == 'mark_as_cancelled' or self.action == 'mark_as_served' or self.action == 'start':
            return serializers.Serializer
        elif self.action == 'shift_window':
            return ShiftWindow
        else:    
            return super().get_serializer_class()


    def get_queryset(self):
        queryset = Customer.objects.filter(created_at__date=date.today()) 

        if self.action == 'get_customers_in_queue':
            queryset = queryset.order_by('position')
        else:
            queryset = queryset.order_by('created_at')

        return queryset



    def get_permissions(self):
        a = self.action
        if a in ['get_customers_in_queue', 'get_waiting_list', 'start', 'shift_list', 'call', 'move_to_the_end']:
            return [IsOperator()]
        elif a in ['mark_as_served', 'mark_as_cancelled', 'shift_window']:
            return [IsOperator(), IsOperatorOfCustomer()]
        return super().get_permissions()


    def get_serializer_context(self):
        context = super().get_serializer_context() 
        context.update({'request': self.request})  
        return context


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        current_time = datetime.now().date()  # Текущее времени
        queue = serializer.validated_data.get('queue')
        branch = queue.branch

        holiday = Calendar.objects.filter(branch=branch, date=current_time)
        if holiday.exists():
            return Response({'error': 'В этот день филиал не работет!'}, status=400)


        self.perform_create(serializer)

        # Получение ID созданного объекта Customer
        customer_id = serializer.instance.id

        # Формирование URL для перенаправления
        redirect_url = config("BASE_URL")+reverse('printing-detail', args=[customer_id])  # 'printing-detail' - имя URL-маршрута, customer_id - аргумент

        headers = self.get_success_headers(serializer.data)
        response = Response({'customer_id': customer_id, 'redirect_url': redirect_url}, status=201, headers=headers)


        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return response



class PrintingView(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        try:
            customer = Customer.objects.get(pk=pk)  # Получение объекта талона по номеру 
        except Customer.DoesNotExist:
            return Response({'error': 'Талон с указанным номером не найден'}, status=404)  # Возврат ошибки 404, если талон с указанным номером не найден

        current_time = datetime.now().time()  # Текущее времени
        queue = customer.queue
        start_time = queue.branch.schedule_start  # Задание начала рабочего дня
        end_time = queue.branch.schedule_end  # Задание конца рабочего дня

        if not (start_time <= current_time <= end_time):  # Проверка на рабочее время
            return Response({'error': 'Печать талонов недоступна в данный момент'}, status=403)  # Возврат ошибки 403


        if customer.is_served is not None:
            return Response({'error': 'Невозможно распечатать талон, т.к. он уже обслужен'}, status=403)


        def calculate_estimated_wait_time(queue, customer):
            ahead_customers = Customer.objects.filter(queue=queue, is_served=None, position__lt=customer.position)
            average_waiting_time = queue.average_waiting_time or 0

            total_waiting_time = (customer.position - 1) * average_waiting_time

            estimated_wait_time = datetime.now() + timedelta(minutes=total_waiting_time)
            time_remaining = estimated_wait_time - datetime.now()

            minutes = time_remaining.seconds // 60
            seconds = time_remaining.seconds % 60

            if minutes == 1439 and seconds == 59:
                minutes, seconds = 0, 0
                
            time_remaining_str = f"{minutes} минут, {seconds} секунд"

            return time_remaining_str

        ticket_data = {
            'ID': customer.pk,
            'Номер талона': customer.ticket_number,
            'Очередь': customer.queue.name,
            'Тип услуги': customer.queue.services.name, 
            'Позиция': customer.position,
            'Выдано': customer.created_at,  
            'Имя посетителя': f'{customer.first_name} {customer.last_name} {customer.surname}',
            'Статус': customer.is_served, 
            'Наименование организации': 'RSK',
            'Филиал': customer.queue.branch.street,
            # 'Количество посетителей в очереди': Customer.objects.filter(queue=customer.queue, is_served=None, ticket_number__lt=customer.ticket_number).count(),  
            'Примерное время ожидания': calculate_estimated_wait_time(customer.queue, customer), 
        }
        return Response(ticket_data)  



