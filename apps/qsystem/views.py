from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.urls import reverse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.branches.models import BaseCalendar, Calendar, Window
from apps.report_apps.customer_reports.models import CustomerAction

from .models import Customer, Queue
from .permissions import IsAdmin, IsAdminOfHisBranch
from .serializers import CustomerSerializer, QueueSerializer


class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    
    def get_permissions(self):
        if self.action == 'get_documents':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

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
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]

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

        if queue.is_blocked == True:
            return Response({'error': 'В данный момент очередь недоступна!'}, status=400)

        base_holiday = BaseCalendar.objects.filter(date=current_time)
        if base_holiday.exists():
            return Response({'error': 'В этот день филиалы не работают!'})
        
        holiday = Calendar.objects.filter(branch=branch, date=current_time)
        if holiday.exists():
            return Response({'error': 'В этот день филиал не работет!'}, status=400)
        
        self.perform_create(serializer)

        customer_id = serializer.instance.id

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

        action = Customer.objects.get(pk=customer_id)
        CustomerAction.objects.create(customer=action, action='created', event=f'Создан талон {action.ticket_number}')

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

        print_start = queue.print_start
        print_end = queue.print_end

        if not (start_time <= current_time <= end_time):  # Проверка на рабочее время
            return Response({'error': 'Печать талонов недоступна в данный момент'}, status=403)  # Возврат ошибки 403

        if not (print_start <= current_time <= print_end): 
            return Response({'error': 'Печать талонов недоступна в данный момент'}, status=403)

        if customer.is_served is not None:
            return Response({'error': 'Невозможно распечатать талон, т.к. он уже обслужен'}, status=403)

        ticket_data = {
            'ID': customer.pk,
            'Номер талона': customer.ticket_number,
            'Очередь': customer.queue.name,
            'Тип услуги': customer.queue.services.name, 
            'Позиция': customer.position,
            'Выдано': customer.created_at,  
            'Филиал': customer.queue.branch.name,
            'Примерное время ожидания': self.calculate_estimated_wait_time(customer.queue, customer), 
        }
        return Response(ticket_data)  
    

    def calculate_estimated_wait_time(self, queue, customer):
        ahead_customers = Customer.objects.filter(queue=queue, is_served=None, position__lt=customer.position)
        average_waiting_time = queue.average_waiting_time or 0
        total_waiting_time = (customer.position - 1) * average_waiting_time

        windows = Window.objects.filter(operator__queues__in=[queue], is_online=True).count()

        if windows <= 0:
            return None

        # Расчитать время ожидания для одного окна оператора
        time_per_window = total_waiting_time / windows

        # Рассчитать общее время ожидания, учитывая количество окон
        total_waiting_time /= windows

        estimated_wait_time = datetime.now() + timedelta(minutes=total_waiting_time)
        time_remaining = estimated_wait_time - datetime.now()

        minutes = time_remaining.seconds // 60
        seconds = time_remaining.seconds % 60

        if minutes == 1439 and seconds == 59:
            minutes, seconds = 0, 0

        time_remaining_str = f"{minutes} минут, {seconds} секунд"

        return time_remaining_str



