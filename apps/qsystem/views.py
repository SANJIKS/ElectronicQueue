from datetime import datetime, timedelta, time, date
from pytz import timezone as timez

from django.urls import reverse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField, Count
from decouple import config
from django.db.models import Max
from django.utils.text import slugify

from .permissions import IsOperator


from .models import Queue, Customer, Waiting_List
from .serializers import GetQueueCustomersSerializer, QueueSerializer, CustomerSerializer, WaitingListSerializer
from apps.branches.models import Window


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
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = Customer.objects.all()

        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time()).astimezone(timez('Asia/Bishkek'))
        end_of_day = datetime.combine(today, datetime.max.time()).astimezone(timez('Asia/Bishkek'))
        queryset = queryset.filter(created_at__gte=start_of_day, created_at__lte=end_of_day)

        queryset = queryset.annotate(
            is_regular=Case(
                When(category='regular', then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('is_regular', 'position', 'created_at')

        return queryset  

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

    
    @action(detail=True, methods=['post'])
    def post_on_waiting_list(self, request, pk=None):
        customer = self.get_object()

        if hasattr(customer, 'waiting_list'):
            return Response({'message': 'Талон уже в списке ожидания!'})  
        
        queue = customer.queue

        customer.position = 0
        customer.save()

        other_customers = queue.customers.exclude(pk=pk)

        for other_customer in other_customers:
            other_customer.position -= 1
            other_customer.save()
              
        waiting_list = Waiting_List.objects.create(customer=customer)

        customer.window = None
        customer.operator = None
        customer.served_start = None
        customer.save()

        return Response({'message': 'Талон добавлен в список ожидания'}, status=200)
    

    @action(detail=False, methods=['get'])
    def get_waiting_list(self, request):
        operator = self.request.user

        queue_ids = operator.queues.values_list('id', flat=True)
        waiting_list = Waiting_List.objects.filter(customer__queue_id__in=queue_ids)

        serializer = WaitingListSerializer(waiting_list, many=True)

        return Response(serializer.data, status=200)


        

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        try:
            waiting_list = Waiting_List.objects.get(customer=customer)
            waiting_list.delete()

        except Waiting_List.DoesNotExist:
            pass

        queue = customer.queue
        current_position = customer.position

        other_customers = queue.customers.exclude(pk=pk)

        for other_customer in other_customers:
            if other_customer.position > current_position:
                other_customer.position -= 1
                other_customer.save()
        customer.operator = self.request.user
        customer.served_start = timezone.now()
        customer.window = self.request.user.window
        customer.save()
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
        

    @action(detail=False, methods=['get'])
    def get_customers_in_queue(self, request):
        operator = self.request.user  # Получение текущего оператора (пользователя)
        queue = operator.queues.all()  # Получение очереди оператора
        
        if not queue:
            return Response({'error': 'Сотрудник не привязан к очереди'}, status=404)


        queryset = Customer.objects.filter(queue__in=queue, is_served__isnull=True)  # Получение первого пользователя в очереди

        today = datetime.now().astimezone(timez('Asia/Bishkek'))
        start_of_day = datetime.combine(today.date(), time.min).astimezone(timez('Asia/Bishkek'))
        end_of_day = datetime.combine(today.date(), time.max).astimezone(timez('Asia/Bishkek'))
        queryset = queryset.filter(created_at__gte=start_of_day, created_at__lte=end_of_day)  

        queryset = queryset.annotate(
            is_regular=Case(
                When(category='regular', then=Value(False)),
                default=Value(True),
                output_field=BooleanField()
            )
        ).order_by('-is_regular', 'position')
        


        serializer = GetQueueCustomersSerializer(queryset, many=True)
        return Response(serializer.data)
    
    
    @action(detail=False, methods=['get'])
    def shift_list(self, request):
        operator = self.request.user
        shifted_tickets = Customer.objects.filter(old_operator=operator)

        serializer = GetQueueCustomersSerializer(shifted_tickets, many=True)

        return Response(serializer.data, status=200)

    @action(detail=True, methods=['patch'])
    def shift_window(self, request, pk=None):
        customer = self.get_object()

        # Получаем данные о новой очереди
        new_window_id = request.data.get('window')  # ID новой очереди


        try:
            new_window = Window.objects.get(id=new_window_id)
        except Window.DoesNotExist:
            return Response({'message': 'Такого окна нет.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if customer.served_start is None:
            return Response({'message': 'Вы не можете перевести талон который не обслуживаете!'}, status=status.HTTP_400_BAD_REQUEST)

        if customer.window == new_window:
            return Response({'message': 'Талон уже обслуживается этим окном.'}, status=status.HTTP_400_BAD_REQUEST)

        if customer.window.number_of_transfers == customer.window.max_transfers:
            return Response({'message': 'Вы слишком много переводили талоны.'}, status=status.HTTP_400_BAD_REQUEST)    

        # Переносим талон на другое окно
        old_window = customer.window
        old_position = customer.position
        old_operator = customer.operator
        old_window.number_of_transfers += 1
        old_window.save()

        customer.window = new_window
        customer.position = new_window.customers.count() + 1  # Позиция становится последней в новой очереди
        customer.operator = new_window.operator
        customer.old_operator = old_operator
        customer.save()

        # Обновляем позиции для остальных талонов в предыдущей очереди
        customers_to_update = old_window.customers.filter(position__gt=old_position)
        for c in customers_to_update:
            c.position -= 1
            c.save()

        return Response({'message': 'Талон успешно перенесен на другую очередь.'})


    

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        customer = self.get_object()

        if customer.served_start is None or customer.operator != self.request.user:
            return Response({'message': 'Вы не обслуживаете этот талон!'}, status=status.HTTP_400_BAD_REQUEST)
        


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
        return Response({'message': 'Талон обслужен и среднее время обновлено'})

    

    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
        customer = self.get_object()

        if customer.served_start is None or customer.operator != self.request.user:
            return Response({'message': 'Вы не обслуживаете этот талон!'}, status=status.HTTP_400_BAD_REQUEST)

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
    
    
    @action(detail=True, methods=['get'])
    def call(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        
        if customer.number_of_calls == 5:
            customer.is_served = False
            current_position = customer.position
            customer.position = 0
            customer.save()

            queue = customer.queue
            other_customers = queue.customers.exclude(pk=pk)

            for other_customer in other_customers:
                if other_customer.position > current_position:
                    other_customer.position -= 1
                    other_customer.save()

            return Response({'message': 'Талон посетителя закрыт!'})
        
        customer.number_of_calls += 1
        customer.save()

        return Response({'message': f'{customer.ticket_number}-{customer.user.profile.first_name}-{customer.user.profile.last_name} IDI SUDA'}, status=200)


    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        
        if customer.is_served == False:
            return Response({'message': 'Талон посетителя уже закрыт!'})
        
        customer.is_served = False
        current_position = customer.position
        customer.position = 0
        customer.save()

        queue = customer.queue

        other_customers = queue.customers.exclude(pk=pk)

        for other_customer in other_customers:
            if other_customer.position > current_position:
                other_customer.position -= 1
                other_customer.save()

        return Response({'message': 'Талон посетителя закрыт'})


    @action(detail=True, methods=['post'])
    def move_to_the_end(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        queue = customer.queue

        current_position = customer.position 

        customer.position = queue.customers.count() + 1
        customer.save()

        other_customers = queue.customers.exclude(pk=pk)

        for other_customer in other_customers:
            if other_customer.position > current_position:
                other_customer.position -= 1
                other_customer.save()

        return Response({'message': 'Талон перемещен в конец очереди.'})
    
    @action(detail=False, methods=['post'])
    def change_status(self, request):
        operator = self.request.user
        if operator.window.is_online == False:
            operator.window.is_online = True
            operator.window.save()
            return Response({'status': 'Online'})
        else:
            operator.window.is_online = False
            operator.window.save()
            return Response({'status': 'Offline'})



class PrintTicket(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        try:
            customer = Customer.objects.get(pk=pk)  # Получение объекта талона по номеру 
        except Customer.DoesNotExist:
            return Response({'error': 'Талон с указанным номером не найден'}, status=404)  # Возврат ошибки 404, если талон с указанным номером не найден

        current_time = datetime.now().time()  # Текущее времени
        queue = customer.queue
        start_time = time(queue.branch.schedule_start)  # Задание начала рабочего дня
        end_time = time(queue.branch.schedule_end)  # Задание конца рабочего дня

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



