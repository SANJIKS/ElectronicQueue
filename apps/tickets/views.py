from datetime import date, datetime

from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone as timez
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.report_apps.operator_reports.models import OperatorAction
from apps.report_apps.customer_reports.models import CustomerAction
from apps.booking.models import Booking
from apps.booking.serializers import BookingSerializer
from apps.branches.models import Branch, Window
from apps.qsystem.models import Customer, Waiting_List
from apps.qsystem.serializers import (CustomerSerializer,
                                      GetQueueCustomersSerializer,
                                      WaitingListSerializer)

from .permissions import IsOperatorOffline, IsOperatorOfCustomer, OperatorIsNotBusy, IsRegistrator, IsOperator
from .serializers import (ChangeNotes, GetByProps, GetServedCustomers,
                          GetWindowsSerializer)
from .tasks import calculate_average_waiting_time, cancel_ticket, shift_positions

today = datetime.now().astimezone(timez('Asia/Bishkek'))


class OperatorViewSet(viewsets.ViewSet):
    def get_permissions(self):
        a = self.action
        if a == 'change_status':
            return [IsOperatorOffline()]
        elif a == 'call' or a == 'start':
            return [OperatorIsNotBusy(), IsOperator()]
        elif a == 'post_on_waiting_list' or a == 'shift_window' or 'mark_as_served' or 'mark_as_cancelled':
            return [IsOperator(), IsOperatorOfCustomer()]
        elif a == 'move_to_the_end':
            return [IsOperator()]


    @action(detail=False, methods=['post'])
    def change_status(self, request):
        """
        Эндпоинт для смены статуса оператора(Онлайн или Оффлайн) 
        """
        operator = self.request.user
        if not operator.window.is_online:
            operator.window.is_online = True
            operator.window.save()
            return Response({'status': 'Online'})
        
        operator.window.is_online = False
        operator.window.save()
        return Response({'status': 'Offline'})


    @action(detail=True, methods=['get'])
    def call(self, request, pk=None):
        """
        Эндпоинт для вызова талона к оператору
        Если посетитель не подходит 5-й раз, его талон отменяется
        """
        customer = Customer.objects.get(pk=pk)
        
        if customer.queue.auto_transfer:
            cancel_ticket.apply_async(args=[customer.id], countdown=customer.queue.waiting_time_operator)

        customer.number_of_calls += 1
        customer.save()

        return Response({'message': f'{customer.ticket_number}-{customer.first_name}-{customer.last_name}, подойдите пожалуйста к {self.request.user.window.number} окну'}, status=200)


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

        window = self.request.user.window
        
        queue = customer.queue.pk
        current_position = customer.position
        shift_positions.delay(pk, queue, current_position)

        customer.operator = self.request.user
        customer.served_start = timezone.now()
        customer.window = window
        customer.save()

        window.is_busy = True
        window.save()

        OperatorAction.objects.create(operator=self.request.user, action='started', event=f'Начал обслуживать талон {customer.ticket_number}')

        serializer = CustomerSerializer(customer)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=['post'])
    def post_on_waiting_list(self, request, pk=None):
        """
        Эндпоинт для перевода талона в лист ожидания
        Нужно передать ID талона
        """
        customer = Customer.objects.get(pk=pk)

        if hasattr(customer, 'waiting_list'):
            return Response({'message': 'Талон уже в списке ожидания!'})  
        
        queue = customer.queue.pk
        current_position = customer.position

        customer.position = 0
        customer.save()

        shift_positions.delay(pk, queue, current_position)

        waiting_list = Waiting_List.objects.create(customer=customer)

        customer.window = None
        customer.operator = None
        customer.served_start = None
        customer.save()

        customer.operator.window.is_busy = False
        customer.operator.window.save()

        return Response({'message': 'Талон добавлен в список ожидания'}, status=200)
    

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'window': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['window']
        ),
        operation_summary="Перенос окна другому оператору(окну)",
        operation_description="Эндпоинт для переноса талона другому окну, другое окно становится занятым, а нынешнее освобождается, нужно передать ID окна и ID талона. Оператор должен обслуживать данный талон для того чтобы перевести на другое окно.",
    )
    @action(detail=True, methods=['patch'])
    def shift_window(self, request, pk=None):
        """
        Эндпоинт для перевода талона в другое окно(другому оператору)
        Блокировка передачи при превышении лимита
        Необходимо передать ID окна и ID талона
        """
        customer = Customer.objects.get(pk=pk)
        new_window_id = request.data.get('window')  

        try:
            new_window = Window.objects.get(id=new_window_id)
        except Window.DoesNotExist:
            return Response({'message': 'Такого окна нет.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if customer.window == new_window:
            return Response({'message': 'Талон уже обслуживается этим окном.'}, status=status.HTTP_400_BAD_REQUEST)

        if customer.window.number_of_transfers == customer.window.max_transfers:
            return Response({'message': 'Вы слишком много переводили талоны.'}, status=status.HTTP_400_BAD_REQUEST)    

        
        old_window = customer.window
        old_window.is_busy = False
        old_window.number_of_transfers += 1
        old_window.save()

        old_operator = customer.operator

        customer.window = new_window
        customer.operator = new_window.operator
        customer.old_operator = old_operator
        customer.save()
    
        new_window.is_busy = True
        new_window.save()

        OperatorAction.objects.create(operator=old_operator, action='shifted', event=f'Талон {customer.ticket_number} был переведен на {new_window.number} окно')
        CustomerAction.objects.create(customer=customer, action='cancelled', event=f'Талон {customer.ticket_number} был переведен на {new_window.number} окно')

        return Response({'message': 'Талон успешно перенесен на другую очередь.'})
    

    @action(detail=True, methods=['post'])
    def move_to_the_end(self, request, pk=None):
        """
        Эндпоинт для перевода талона в конец очереди, поле position сменяется на последнее
        Нужно передать ID талона
        """
        customer = Customer.objects.get(pk=pk)

        queue = customer.queue.pk
        current_position = customer.position 
        shift_positions.delay(pk, queue, current_position)

        customer = Customer.objects.get(pk=pk)
        customer.position = Customer.objects.filter(queue=queue, created_at__date=today, is_served=None).count()
        customer.save()

        return Response({'message': 'Талон перемещен в конец очереди.'})
    

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        """
        Эндпоинт для обновления статуса обслуживания талона как "Обслужен"
        Сделать это может только тот оператор, который обслуживает данный талон
        Нужно передать ID талона
        """
        customer = Customer.objects.get(pk=pk)
        
        if customer.is_served:
            return Response({'message': 'Талон уже обслужен.'})
    

        customer.operator.window.is_busy = False
        customer.operator.window.save()

        customer.is_served = True
        customer.served_at = timezone.now()
        customer.position = 0
        customer.save()

        queue = customer.queue.pk
        calculate_average_waiting_time.delay(queue)

        OperatorAction.objects.create(operator=customer.operator, action='served', event=f'Обслужил талон {customer.ticket_number}')
        CustomerAction.objects.create(customer=customer, action='served', event=f'Талон {customer.ticket_number} был обслужен')

        return Response({'message': 'Талон обслужен и среднее время обновлено'})
    

    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
        """
        Эндпоинт для обновления статуса обслуживания талона как "Отменен"
        Сделать это может только тот оператор, который обслуживает данный талон
        Нужно передать ID талона
        """
        customer = Customer.objects.get(pk=pk)

        if customer.is_served == False:
            return Response({'message': 'Талон уже отменен.'})
            

        customer.operator.window.is_busy = False
        customer.operator.window.save()

        customer.is_served = False
        customer.position = 0
        customer.save()

        OperatorAction.objects.create(operator=customer.operator, action='cancelled', event=f'Отменил талон {customer.ticket_number}')
        CustomerAction.objects.create(customer=customer, action='cancelled', event=f'Талон {customer.ticket_number} был отменен')

        return Response({'message': 'Талон отменен.'})


class OperatorGetViewSet(viewsets.ViewSet):   
    @action(detail=False, methods=['get'])
    def get_customers_in_queue(self, request):
        """
        Эндпоинт для получения талонов в очередях которые обслуживает оператор
        """
        queue = self.request.user.queues.all()  
        
        if not queue:
            return Response({'error': 'Сотрудник не привязан к очереди'}, status=404)

        queryset = Customer.objects.filter(queue__in=queue, is_served=None, created_at__date=today, old_operator=None, operator=None).order_by('position')
        
        serializer = GetQueueCustomersSerializer(queryset, many=True)
        return Response(serializer.data, status=200)

    @action(detail=False, methods=['get'])
    def get_my_customer(self, request):
        queryset = Customer.objects.get(operator=self.request.user, is_served=None, served_start__date=today)
        serializer = CustomerSerializer(queryset)
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
    def get_windows_for_transfer(self, request):
        operator = self.request.user
        queue_ids = operator.queues.values_list('id', flat=True)

        windows = Window.objects.filter(
            operator__queues__id__in=queue_ids,  # Фильтр по принадлежности к очереди оператора
            is_busy=False,   # Фильтр по свободному окну
            is_online=True  # Фильтр по онлайн-статусу окна
        )

        serializer = GetWindowsSerializer(windows, many=True, context={'operator': operator})
        return Response(serializer.data, status=200)


    @action(detail=False, methods=['get'])
    def get_cancelled_customers(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(created_at__date=today, operator=operator, is_served=False)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get'])
    def get_served_customers(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(created_at__date=today, operator=operator, is_served=True)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get'])
    def get_served_customers_all(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(operator=operator, is_served=True)
        serializer = GetServedCustomers(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegistratorViewSet(viewsets.ViewSet):
    permission_classes = [IsRegistrator]
    @action(detail=True, methods=['get'])
    def get_today_tickets(self, request, pk=None):
        """
        Эндпоинт для регистратора
        Получение всех выданных талонов на сегодняшний день
        Нужно передать ID филиала
        """
        try:
            branch = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        tickets = Customer.objects.filter(queue__branch=branch, created_at__date=today)

        serializer = CustomerSerializer(tickets, many=True)
        return Response(serializer.data)
    

    @action(detail=True, methods=['get'])
    def get_bookings(self, request, pk=None):
        today = date.today()
        bookings = Booking.objects.filter(queue__branch=pk, date__gte=today)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        request_body=GetByProps,
        operation_summary="Перенос окна другому оператору(окну)",
        operation_description="Эндпоинт для переноса талона другому окну, другое окно становится занятым, а нынешнее освобождается, нужно передать ID окна и ID талона. Оператор должен обслуживать данный талон для того чтобы перевести на другое окно.",
    )
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
    

    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        request_body=GetByProps,
        operation_summary="Перенос окна другому оператору(окну)",
        operation_description="Эндпоинт для переноса талона другому окну, другое окно становится занятым, а нынешнее освобождается, нужно передать ID окна и ID талона. Оператор должен обслуживать данный талон для того чтобы перевести на другое окно.",)
    def get_bookings_by_props(self, request):
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

        bookings = Booking.objects.filter(**filters)
        serializer = BookingSerializer(bookings, many=True)

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
            
        current_position = customer.position
        queue = customer.queue

        customer.is_served = False
        customer.position = 0
        customer.save()

        shift_positions(pk, queue, current_position)

        return Response({'message': 'Талон отменен.'})
    

    @action(detail=True, methods=['patch'])
    @swagger_auto_schema(
    request_body=ChangeNotes,
    operation_summary="Перенос окна другому оператору(окну)",
    operation_description="Эндпоинт для переноса талона другому окну, другое окно становится занятым, а нынешнее освобождается, нужно передать ID окна и ID талона. Оператор должен обслуживать данный талон для того чтобы перевести на другое окно.",
    )
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