from datetime import datetime, timedelta, time, date
from pytz import timezone as timez


from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField, Count
from decouple import config
from django.db.models import Max
from django.http import HttpResponseNotAllowed

from drf_yasg.utils import swagger_auto_schema


from rest_framework.views import APIView
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .permissions import IsOperatorOnline, OperatorIsNotBusy
from .models import Profile
from .serializers import ChangeNotes, GetByProps, GetWindowsSerializer, ProfileSerializer
from apps.qsystem.models import Customer, Waiting_List
from apps.qsystem.serializers import CustomerSerializer, GetQueueCustomersSerializer, WaitingListSerializer, ShiftWindow
from apps.qsystem.permissions import IsOperator, IsOperatorOfCustomer
from apps.branches.models import Branch, Window


class ProfileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    

    @action(detail=False, methods=['get'])
    def user_history(self, request):
        """
        Эндпоинт для получения истории талонов пользователя
        """
        user = request.user  # Получение текущего пользователя
        tickets = Customer.objects.filter(user=user)  # Получение всех талонов пользователя

        serializer = CustomerSerializer(tickets, many=True)  
        return Response(serializer.data)
    

class OperatorViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        if self.action == 'change_status' or self.action == 'mark_as_cancelled' or self.action == 'mark_as_served' or self.action == 'start' or self.action == 'post_on_waiting_list' or self.action == 'move_to_the_end':
            return serializers.Serializer
        elif self.action == 'shift_window':
            return ShiftWindow
        else:    
            return super().get_serializer_class()
        

    def get_queryset(self):
        queryset = Customer.objects.none()

        if self.action == 'get_customers_in_queue':
            queryset = Customer.objects.filter(created_at__date=date.today()).order_by('position')
        elif self.action in ['mark_as_cancelled', 'mark_as_served', 'post_on_waiting_list', 'shift_window']:
            queryset = Customer.objects.filter(created_at__date=date.today(), is_served__isnull=True).order_by('created_at')
        return queryset

    def get_permissions(self):
        a = self.action
        if a == 'change_status':
            return [IsOperatorOnline()]
        elif a == 'start':
            return [OperatorIsNotBusy]
        elif a in ['get_customers_in_queue', 'get_waiting_list', 'shift_list', 'call', 'move_to_the_end']:
            return [IsOperator()]
        elif a in ['mark_as_served', 'mark_as_cancelled', 'shift_window']:
            return [IsOperator(), IsOperatorOfCustomer()]
        return super().get_permissions()
    

    def create(self, request, *args, **kwargs):
        return Response({'message': 'Воспользуйтесь customers/'})

    def retrieve(self, request, *args, **kwargs):
        return Response({'message': 'Воспользуйтесь customers/'})

    def update(self, request, *args, **kwargs):
        return Response({'message': 'Воспользуйтесь customers/'})

    def partial_update(self, request, *args, **kwargs):
        return Response({'message': 'Воспользуйтесь customers/'})

    def destroy(self, request, *args, **kwargs):
        return Response({'message': 'Воспользуйтесь customers/'})
    

    @action(detail=False, methods=['post'])
    def change_status(self, request):
        """
        Эндпоинт для смены статуса оператора(Онлайн или Оффлайн) 
        """
        operator = self.request.user
        if operator.window.is_online == False:
            operator.window.is_online = True
            operator.window.save()
            return Response({'status': 'Online'})
        else:
            operator.window.is_online = False
            operator.window.save()
            return Response({'status': 'Offline'})
        
    
    @action(detail=False, methods=['get'])
    def get_customers_in_queue(self, request):
        """
        Эндпоинт для получения талонов в очередях которые обслуживает оператор
        """
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
    

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Эндпоинт для начала обслуживания
        Нужно передать ID талона
        После чего поле operator у талона сменяется на того от кого пришел запрос
        Поле served_start меняется на текущее время
        """
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
        self.request.user.window.is_busy = True
        customer.served_start = timezone.now()
        customer.window = self.request.user.window
        customer.save()

        window = self.request.user.window
        window.is_busy = True
        window.save()
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
    

    @action(detail=True, methods=['get'])
    def call(self, request, pk=None):
        """
        Эндпоинт для вызова талона к оператору
        Если посетитель не подходит 5-й раз, его талон отменяется
        """
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
    def post_on_waiting_list(self, request, pk=None):
        """
        Эндпоинт для перевода талона в лист ожидания
        Нужно передать ID талона
        """
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
        customer.operator.window.is_busy = False
        customer.operator = None
        customer.served_start = None
        customer.save()

        return Response({'message': 'Талон добавлен в список ожидания'}, status=200)
    


    @action(detail=False, methods=['get'])
    def get_waiting_list(self, request):
        """
        Эндпоинт для получения списка ожидания
        """
        operator = self.request.user

        queue_ids = operator.queues.values_list('id', flat=True)
        waiting_list = Waiting_List.objects.filter(customer__queue_id__in=queue_ids)

        serializer = WaitingListSerializer(waiting_list, many=True)

        return Response(serializer.data, status=200)
    

    @action(detail=False, methods=['get'])
    def get_all_windows(self, request):
        branch = self.request.user.window.branch
        windows = Window.objects.filter(branch=branch)
        serializer = GetWindowsSerializer(windows, many=True, context={'operator': self.request.user})
        return Response(serializer.data, status=200)


    @action(detail=False, methods=['get'])
    def shift_list(self, request):
        """
        Эндпоинт для получения списка переведенных в другое окно талонов
        """
        operator = self.request.user
        shifted_tickets = Customer.objects.filter(old_operator=operator)

        serializer = GetQueueCustomersSerializer(shifted_tickets, many=True)

        return Response(serializer.data, status=200)
    

    @action(detail=True, methods=['patch'])
    def shift_window(self, request, pk=None):
        """
        Эндпоинт для перевода талона в другое окно(другому оператору)
        Блокировка передачи при превышении лимита
        Необходимо передать ID окна и ID талона
        """
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
        old_window.is_busy = False
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
    def move_to_the_end(self, request, pk=None):
        """
        Эндпоинт для перевода талона в конец очереди, поле position сменяется на последнее
        Нужно передать ID талона
        """
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
    

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        """
        Эндпоинт для обновления статуса обслуживания талона как "Обслужен"
        Сделать это может только тот оператор, который обслуживает данный талон
        Нужно передать ID талона
        """
        customer = self.get_object()

        if customer.served_start is None or customer.operator != self.request.user:
            return Response({'message': 'Вы не обслуживаете этот талон!'}, status=status.HTTP_400_BAD_REQUEST)
        


        if customer.is_served:
            return Response({'message': 'Талон уже обслужен.'})
    
        customer.is_served = True
        customer.served_at = timezone.now()
        customer.position = 0
        customer.operator.window.is_busy = False
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
        """
        Эндпоинт для обновления статуса обслуживания талона как "Отменен"
        Сделать это может только тот оператор, который обслуживает данный талон
        Нужно передать ID талона
        """
        customer = self.get_object()

        if customer.served_start is None or customer.operator != self.request.user:
            return Response({'message': 'Вы не обслуживаете этот талон!'}, status=status.HTTP_400_BAD_REQUEST)

        if customer.is_served == False:
            return Response({'message': 'Талон уже отменен.'})
            
        customer.is_served = False
        customer.position = 0
        customer.operator.window.is_busy = False
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
    def get_cancelled_customers(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(created_at__date=date.today(), operator=operator, is_served=False)
        print(customers)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class RegistratorViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['get'])
    def get_today_tickets(self, request, pk=None):
        """
        Эндпоинт для регистратора
        Получение всех выданных талонов на сегодняшний день
        Нужно передать ID филиала
        """
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            branch = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()

        tickets = Customer.objects.filter(queue__branch=branch, created_at__date=today)

        serializer = CustomerSerializer(tickets, many=True)
        return Response(serializer.data)
    

    @action(detail=True, methods=['patch'])
    @swagger_auto_schema(
    request_body=ChangeNotes)
    def write_info(self, request, pk=None):
        """
        Эндпоинт для внесения доп. сведений о талоне(посетителе)
        Нужно передать ID талона и в json передать notes: "инфо"
        """
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        notes = request.data.get('notes')
        customer.notes = notes
        customer.save()
        
        return Response(status=status.HTTP_200_OK)

    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
    request_body=GetByProps)
    def customer_by_props(self, request):
        """
        Эндпоинт для поиска талонов по различным реквизитам
        """
        filters = {}
        if 'first_name' in request.data and request.data['first_name'] != "":
            filters['first_name'] = request.data['first_name']
        if 'last_name' in request.data and request.data['last_name'] != "":
            filters['last_name'] = request.data['last_name']
        if 'surname' in request.data and request.data['surname'] != "":
            filters['surname'] = request.data['surname']
        if 'phone' in request.data and request.data['phone'] != "":
            filters['phone_number'] = request.data['phone']
        if 'pasport' in request.data and request.data['pasport'] != "":
            filters['pasport'] = request.data['pasport']
        
        customers = Customer.objects.filter(**filters)

        serializer = CustomerSerializer(customers, many=True)

        return Response(serializer.data, status=200)
    

    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
        """
        Эндпоинт для обновления статуса обслуживания талона как "Отменен"
        Для регистратора
        """
        customer = Customer.objects.get(pk=pk)

        if customer.is_served == False:
            return Response({'message': 'Талон уже отменен.'})
            
        customer.is_served = False
        customer.position = 0
        customer.save()

        queue = customer.queue

        current_position = customer.position
        waiting_customers = Customer.objects.filter(queue=queue, is_served=None).order_by('position')
        for waiting_customer in waiting_customers:
            if waiting_customer.position is not None and waiting_customer.position > current_position:
                waiting_customer.position -= 1
                waiting_customer.save()

        return Response({'message': 'Талон отменен.'})