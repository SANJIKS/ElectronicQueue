from datetime import datetime, timedelta, time

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone

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
        return super().get_permissions()  

    def get_serializer_context(self):
        context = super().get_serializer_context() 
        context.update({'request': self.request})  
        return context

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        customer = self.get_object()  # Получение объекта Customer по его идентификатору 
        customer.is_served = True  # Установка is_served в значение True
        customer.served_at = timezone.now()  # Установка времени обслуживания на текущее время
        customer.save()  # Сохранение изменений 

        queue = customer.queue  # Получение объекта очереди
        served_customers = Customer.objects.filter(queue=queue, is_served=True)  # Получение всех обслуженных талонов для данной очереди
        total_served_customers = served_customers.count()  # Получение общего количества обслуженных талонов
        
        total_waiting_time = sum(
            (customer.served_at - customer.created_at).seconds // 60 for customer in served_customers
        )  # Вычисление общего времени ожидания для обслуженных талонов (в минутах)
        average_waiting_time = (
            total_waiting_time // total_served_customers if total_served_customers > 0 else 0
        )  # Вычисление среднего времени ожидания (в минутах) или установка в 0, если нет обслуженных талонов

        queue.average_waiting_time = average_waiting_time  # Установка среднего времени ожидания для очереди
        queue.save()  # Сохранение изменений

        return Response({'message': 'Талон обслужен и среднее время обновлено'})  

    



class PrintTicket(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        current_time = datetime.now().time()  # Текущее времени
        start_time = time(9, 0)  # Задание начала рабочего дня
        end_time = time(22, 59)  # Задание конца рабочего дня

        if not (start_time <= current_time <= end_time):  # Проверка на рабочее время
            return Response({'error': 'Печать талонов недоступна в данный момент'}, status=403)  # Возврат ошибки 403

        try:
            customer = Customer.objects.get(ticket_number=pk)  # Получение объекта талона по номеру 
        except Customer.DoesNotExist:
            return Response({'error': 'Талон с указанным номером не найден'}, status=404)  # Возврат ошибки 404, если талон с указанным номером не найден

        def calculate_estimated_wait_time(queue, customer):
            ahead_customers = Customer.objects.filter(queue=queue, is_served=False, ticket_number__lt=customer.ticket_number)  # Получение всех талонов, находящихся в очереди перед указанным талоном
            average_waiting_time = queue.average_waiting_time or 0  # Получение среднего времени ожидания для очереди или 0, если значение отсутствует

            total_waiting_time = ahead_customers.count() * average_waiting_time  # Вычисление общего времени ожидания для всех талонов перед указанным талоном
            estimated_wait_time = datetime.now() + timedelta(minutes=total_waiting_time)  # Вычисление примерного времени ожидания для указанного талона
            time_remaining = estimated_wait_time - datetime.now()  # Вычисление оставшегося времени ожидания

            minutes = time_remaining.seconds // 60  
            seconds = time_remaining.seconds % 60  

            time_remaining_str = f"{minutes} минут, {seconds} секунд"  

            return time_remaining_str

        ticket_data = {
            'Номер талона': customer.ticket_number, 
            'Выдано': customer.created_at,  
            'Имя посетителя': customer.user.username, 
            'Наименование организации': 'RSK',  
            'Очередь': customer.queue.name, 
            'Номер окна': customer.queue.window_number, 
            'Количество посетителей в очереди': Customer.objects.filter(queue=customer.queue, is_served=False, ticket_number__lt=customer.ticket_number).count(),  
            'Примерное время ожидания': calculate_estimated_wait_time(customer.queue, customer), 
        }
        return Response(ticket_data)  



