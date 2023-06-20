from datetime import datetime, timedelta, time
import re
from django.urls import reverse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from decouple import config

from .permissions import IsOperator

from django.db.models import Max
from django.utils.text import slugify

from .models import Queue, Customer
from .serializers import QueueSerializer, CustomerSerializer

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer

    def get_permissions(self):
        if self.action == 'create' and not self.request.user.is_superuser:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all() 
    serializer_class = CustomerSerializer  

    def get_permissions(self):
        if self.action == 'create': 
            return [permissions.IsAuthenticated()]  
        elif self.action == 'mark_as_served' or self.action == 'mark_as_cancelled' or self.action == 'get_customer_info':
            return [IsOperator()]
        return super().get_permissions()


    def get_serializer_context(self):
        context = super().get_serializer_context() 
        context.update({'request': self.request})  
        return context


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Получение ID созданного объекта Customer
        customer_id = serializer.instance.id

        # Формирование URL для перенаправления
        redirect_url = config("BASE_URL")+reverse('printing-detail', args=[customer_id])  # 'printing-detail' - имя URL-маршрута, customer_id - аргумент

        headers = self.get_success_headers(serializer.data)
        return Response({'customer_id': customer_id, 'redirect_url': redirect_url}, status=201, headers=headers)


    @action(detail=False, methods=['get'])
    def get_customer_info(self, request):
        operator = self.request.user  # Получение текущего оператора (пользователя)
        queue = operator.queue  # Получение очереди оператора

        if not queue:
            return Response({'error': 'Сотрудник не привязан к очереди'}, status=404)  
        
        first_customer = Customer.objects.filter(queue=queue, is_served=None).order_by('position').first()  # Получение первого пользователя в очереди

        if not first_customer:
            return Response({'error': 'Нет пользователей в очереди'}, status=404)  

        customer_data = {
            'Номер талона': first_customer.ticket_number,
            'Имя посетителя': f"{first_customer.user.profile.first_name} {first_customer.user.profile.last_name}",
            'Статус': first_customer.is_served,
        }

        return Response(customer_data)
    

    @action(detail=True, methods=['post'])
    def change_queue(self, request, pk=None):
        customer = self.get_object()

        # Получаем данные о новой очереди
        new_queue_id = request.data.get('queue')  # ID новой очереди

        try:
            new_queue = Queue.objects.get(id=new_queue_id)
        except Queue.DoesNotExist:
            return Response({'message': 'Указана недопустимая очередь.'}, status=status.HTTP_400_BAD_REQUEST)

        # Переносим талон на новую очередь
        old_queue = customer.queue
        old_position = customer.position

        customer.queue = new_queue
        customer.position = new_queue.customer_set.count() + 1  # Позиция становится последней в новой очереди
        customer.save()

        # Обновляем позиции для остальных талонов в предыдущей очереди
        customers_to_update = old_queue.customer_set.filter(position__gt=old_position)
        for c in customers_to_update:
            c.position -= 1
            c.save()

        return Response({'message': 'Талон успешно перенесен на другую очередь.'})


    

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        customer = self.get_object()

        if customer.is_served:
            return Response({'message': 'Талон уже обслужен.'})
    
        customer.is_served = True
        customer.served_at = timezone.now()
        customer.position = 0
        customer.save()

        queue = customer.queue

        current_position = customer.position

        waiting_customers = Customer.objects.filter(queue=queue, is_served=None).order_by('position')
        for waiting_customer in waiting_customers:
            if waiting_customer.position is not None and waiting_customer.position > current_position:
                waiting_customer.position -= 1
                waiting_customer.save()

        served_customers = Customer.objects.filter(queue=queue, is_served=True)
        total_served_customers = served_customers.count()

        total_waiting_time = sum(
            (customer.served_at - customer.created_at).seconds // 60 for customer in served_customers
        )
        average_waiting_time = (
            total_waiting_time // total_served_customers if total_served_customers > 0 else 0
        )

        queue.average_waiting_time = average_waiting_time
        queue.save()


        operator = queue.operator
        serving_time = customer.served_at - customer.created_at
        operator.queue.kpi += serving_time.total_seconds() / 60 
        operator.save()

        return Response({'message': 'Талон обслужен и среднее время обновлено'})

    

    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
        customer = self.get_object()

        if not customer.is_served:
            return Response({'message': 'Талон уже отменен.'})
            
        customer.is_served = False
        customer.position = 0
        customer.save()

        queue = customer.queue

        # Обновление position для остальных талонов в очереди
        current_position = customer.position
        waiting_customers = Customer.objects.filter(queue=queue, is_served=None).order_by('position')
        for waiting_customer in waiting_customers:
            if waiting_customer.position is not None and waiting_customer.position > current_position:
                waiting_customer.position -= 1
                waiting_customer.save()

        return Response({'message': 'Талон отменен.'})

    

    @action(detail=False, methods=['get'])
    def user_history(self, request):
        user = request.user  # Получение текущего пользователя
        tickets = Customer.objects.filter(user=user)  # Получение всех талонов пользователя

        serializer = CustomerSerializer(tickets, many=True)  
        return Response(serializer.data)

    



class PrintTicket(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        current_time = datetime.now().time()  # Текущее времени
        start_time = time(9, 0)  # Задание начала рабочего дня
        end_time = time(22, 59)  # Задание конца рабочего дня

        if not (start_time <= current_time <= end_time):  # Проверка на рабочее время
            return Response({'error': 'Печать талонов недоступна в данный момент'}, status=403)  # Возврат ошибки 403

        try:
            customer = Customer.objects.get(pk=pk)  # Получение объекта талона по номеру 
        except Customer.DoesNotExist:
            return Response({'error': 'Талон с указанным номером не найден'}, status=404)  # Возврат ошибки 404, если талон с указанным номером не найден
        
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
            'Позиция': customer.position,
            'Выдано': customer.created_at,  
            'Имя посетителя': customer.user.username,
            'Статус': customer.is_served, 
            'Наименование организации': 'RSK',
            'Филиал': customer.queue.branch.address,
            'Очередь': customer.queue.name, 
            'Номер окна': customer.queue.window_number,
            'Оператор': customer.queue.operator.username, 
            # 'Количество посетителей в очереди': Customer.objects.filter(queue=customer.queue, is_served=None, ticket_number__lt=customer.ticket_number).count(),  
            'Примерное время ожидания': calculate_estimated_wait_time(customer.queue, customer), 
        }
        return Response(ticket_data)  



