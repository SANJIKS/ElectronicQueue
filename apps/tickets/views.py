from datetime import date, datetime

from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone as timez
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.branches.serializers import WindowSerializer


from apps.report_apps.operator_reports.models import OperatorAction
from apps.report_apps.customer_reports.models import CustomerAction
from apps.booking.models import Booking
from apps.booking.serializers import BookingSerializer
from apps.branches.models import Branch, Window
from apps.qsystem.models import Customer, Waiting_List
from apps.qsystem.serializers import (CustomerSerializer,
                                      GetQueueCustomersSerializer, QueueSerializer,
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

    @swagger_auto_schema(
        operation_summary="Сменить статус оператора(Online/Offline)",
        operation_description="""
        Эндпоинт для смены статуса оператора. Пользователь который отправляет запрос должен быть оператором.""",
    )
    @action(detail=False, methods=['post'])
    def change_status(self, request):
        operator = self.request.user
        if not operator.window.is_online:
            operator.window.is_online = True
            operator.window.save()
            return Response({'status': 'Online'})
        
        operator.window.is_online = False
        operator.window.save()
        return Response({'status': 'Offline'})


    @swagger_auto_schema(
        operation_summary="Вызов посетителя",
        operation_description="Эндпоинт для вызова посетителя к оператору, если автоматический перенос талона в конец очереди включён, то талон будет переноситься в конец очереди через то время, которое указал администратор, и удалятся, после количества вызовов указанным администратором. Оператор должен быть свободен и онлайн. Необходимо передать id талона",
    )
    @action(detail=True, methods=['get'])
    def call(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        
        if customer.queue.auto_transfer:
            cancel_ticket.apply_async(args=[customer.id], countdown=customer.queue.waiting_time_operator)

        customer.number_of_calls += 1
        customer.window = self.request.user.window
        customer.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {}

            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return Response({'message': f'{customer.ticket_number}, подойдите пожалуйста к {self.request.user.window.number} окну'}, status=200)

    @swagger_auto_schema(
        operation_summary="Начать обслуживать",
        operation_description="Эндпоинт для начала обслуживания посетителя, поля window и operator меняются на данного оператора, позиции всех остальных талонов сдвигаются на 1. Оператор должен быть свободен и онлайн. Необходимо передать id талона",
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
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
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        serializer = CustomerSerializer(customer)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Отправить в лист ожидания",
        operation_description="Эндпоинт для отправки посетителя в лист ожидания для заполнения документов или т.п. Для отправки в лист ожидания оператор должен обслуживать этот талон, позиция талона становиться нулевым, для вызова вне очереди позже, а все данные об оператора и окне у талона обнуляются, позиции всех остальных талонов сдвигаются на 1. Необходимо передать id талона.",
    )
    @action(detail=True, methods=['post'])
    def post_on_waiting_list(self, request, pk=None):
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
        customer.served_start = None

        customer.operator.window.is_busy = False
        customer.operator.window.save()
        
        customer.operator = None
        customer.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {'window': self.request.user.window.number}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

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
        operation_description="Эндпоинт для переноса талона другому окну, другое окно становится занятым, а нынешнее освобождается, позиции всех остальных талонов сдвигаются на 1, нужно передать ID окна и ID талона. Оператор должен обслуживать данный талон для того чтобы перевести на другое окно. Создаётся протокол о переносе талона для оператора и талона.",
    )
    @action(detail=True, methods=['patch'])
    def shift_window(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)
        new_window_id = request.data.get('window')  

        try:
            new_window = Window.objects.get(id=new_window_id)
        except Window.DoesNotExist:
            return Response({'message': 'Такого окна нет.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if customer.window == new_window:
            return Response({'message': 'Талон уже обслуживается этим окном.'}, status=status.HTTP_400_BAD_REQUEST)

        if customer.window.number_of_transfers == customer.queue.max_transfers:
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

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {'window': self.request.user.window.number}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return Response({'message': 'Талон успешно перенесен на другую очередь.'})
    

    @swagger_auto_schema(
        operation_summary="Перенести в конец очереди",
        operation_description="Эндпоинт для переноса талона в конец очереди вручную, позиция талона становится последней в очереди, а у остальных позиция сдвигается на 1. Оператор должен быть свободен и онлайн. Необходимо передать id талона.",
    )
    @action(detail=True, methods=['post'])
    def move_to_the_end(self, request, pk=None):
        customer = Customer.objects.get(pk=pk)

        queue = customer.queue.pk
        current_position = customer.position 
        shift_positions.delay(pk, queue, current_position)

        customer = Customer.objects.get(pk=pk)
        customer.position = Customer.objects.filter(queue=queue, created_at__date=today, is_served=None).count()
        customer.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {'window': self.request.user.window.number}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return Response({'message': 'Талон перемещен в конец очереди.'})
    

    @swagger_auto_schema(
        operation_summary="Закончить обслуживание",
        operation_description='Эндпоинт для обонзначения талона как "Обслуженный", и обновления среднего времени ожидания в очереди, создаётся протокол об обслуживании талона для талона и оператора. Необходимо передать id талона, оператор должен обслуживать данный талон',
    )
    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
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

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {'window': self.request.user.window.number}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return Response({'message': 'Талон обслужен и среднее время обновлено'})
    
    @swagger_auto_schema(
        operation_summary="Отменить обслуживание талона",
        operation_description='Эндпоинт для обозначения талона как "Отмененный", среднее время обслуживания не обновляется, создаётся протокол об отменене обслуживания талона для оператора и талона. Необходимо передать id талона, оператор должен обслуживать данный талон.',
    )
    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
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

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "score_broadcast",
            {
                "type": "send_ticket_list",
                "event": {'window': self.request.user.window.number}
 
            }
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "cabinet_broadcast",
            {
                "type": "send_ticket_list",
                "event": {},  
            }
        )

        return Response({'message': 'Талон отменен.'})


class OperatorGetViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="Получить список очередей, которые может обслуживать оператор.",
        operation_description="Эндпоинт для получения списка очередей, которые может обслуживать оператор. Пользователь, который отправляет запрос, должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_operator_queues(self, request):
        queues = self.request.user.queues.all()
        serializer = QueueSerializer(queues, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="Получить окно, которое обслуживает оператор.",
        operation_description="Эндпоинт для получения окна, которое обслуживает оператор. Пользователь, который отправляет запрос, должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_operator_window(self, request):
        window = self.request.user.window
        if not window:
            return Response({'error': 'Оператор не привязан к окну'}, status=404)
        serializer = WindowSerializer(window)
        return Response(serializer.data, status=200)
    
    @swagger_auto_schema(
        operation_summary="Получить список ожидающих талонов.",
        operation_description="Эндпоинт для получения списка талонов которые необходимо обслужить оператору. Возвращается список талонов отфильтрованных по дате, очереди которые обслуживает данный оператор, не обслужены, и те которые не были перенесены на другое окно. Отсортированы по позиции. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_customers_in_queue(self, request):
        queue = self.request.user.queues.all()  
        
        if not queue:
            return Response({'error': 'Сотрудник не привязан к очереди'}, status=404)

        queryset = Customer.objects.filter(queue__in=queue, is_served=None, created_at__date=today, old_operator=None, operator=None).order_by('position')
        
        serializer = GetQueueCustomersSerializer(queryset, many=True)
        return Response(serializer.data, status=200)


    @swagger_auto_schema(
        operation_summary="Получить талон который обслуживает оператор",
        operation_description="Эндпоинт возвращает талон который в данный момент обслуживает оператор. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_my_customer(self, request):
        queryset = Customer.objects.get(operator=self.request.user, is_served=None, served_start__date=today)
        serializer = CustomerSerializer(queryset)
        return Response(serializer.data, status=200)
    

    @swagger_auto_schema(
        operation_summary="Получить список талонов переведенных другому оператору.",
        operation_description="Эндпоинт возвращает список талонов которые оператор перевел на другое окно. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def shift_list(self, request):
        operator = self.request.user
        shifted_tickets = Customer.objects.filter(old_operator=operator)

        serializer = GetQueueCustomersSerializer(shifted_tickets, many=True)

        return Response(serializer.data, status=200)


    @swagger_auto_schema(
        operation_summary="Лист ожидания",
        operation_description="Эндпоинт возвращает лист ожидания в котором находятся талоны, услуги которых обслуживает оператор. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_waiting_list(self, request):
        operator = self.request.user

        queue_ids = operator.queues.values_list('id', flat=True)
        waiting_list = Waiting_List.objects.filter(customer__queue_id__in=queue_ids)

        serializer = WaitingListSerializer(waiting_list, many=True)

        return Response(serializer.data, status=200)
    

    @swagger_auto_schema(
        operation_summary="Получить все окна в филиале",
        operation_description="Эндпоинт возвращает все окна которые есть в филиале в котором работает оператор. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_all_windows(self, request):
        branch = self.request.user.window.branch
        windows = Window.objects.filter(branch=branch)
        serializer = GetWindowsSerializer(windows, many=True, context={'operator': self.request.user})
        return Response(serializer.data, status=200)
    

    @swagger_auto_schema(
        operation_summary="Получить доступные окна для перевода талона",
        operation_description="Эндпоинт возвращает список доступных окон для перевода к посетителя к ним. Окна фильтруются по очереди которые могут обслуживать, они должны быть онлайн и свободны. Пользователь который отправляет запрос должен быть оператором.",
    )
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


    @swagger_auto_schema(
        operation_summary="Получить отмененные талоны оператора",
        operation_description="Эндпоинт возвращает список отмененных талонов за сегодня. Пользователь который отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_cancelled_customers(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(created_at__date=today, operator=operator, is_served=False)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_summary="Получить обслуженные талоны оператора",
        operation_description="Эндпоинт возвращает список обслуженных талонов за сегодня. Пользователь которые отправляет запрос должен быть оператором.",
    )
    @action(detail=False, methods=['get'])
    def get_served_customers(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(created_at__date=today, operator=operator, is_served=True)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_summary="Получить все обслуженные талоны оператора",
        operation_description="""
        Функционал: Эндпоинт возвращает список обслуженных талонов за все время.
        Permissions: Пользователь которые отправляет запрос должен быть оператором"""
    )
    @action(detail=False, methods=['get'])
    def get_served_customers_all(self, request):
        operator = self.request.user

        customers = Customer.objects.filter(operator=operator, is_served=True)
        serializer = GetServedCustomers(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegistratorViewSet(viewsets.ViewSet):
    permission_classes = [IsRegistrator]
    
    @swagger_auto_schema(
        operation_summary="Получить список талонов за сегодня",
        operation_description="""
        Эндпоинт возвращает все талоны за сегодня, и филиала в котором работает регистратор. Пользователь который отправляет запро с должен быть регистратором."""
    )
    @action(detail=True, methods=['get'])
    def get_today_tickets(self, request, pk=None):
        try:
            branch = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        tickets = Customer.objects.filter(queue__branch=branch, created_at__date=today)

        serializer = CustomerSerializer(tickets, many=True)
        return Response(serializer.data)
    

    @swagger_auto_schema(
        operation_summary="Получить список предварительных записей от сегодняшней даты",
        operation_description="""
        Эндпоинт возвращает список пред. записей в филиале в котором работает регистратор, и даты записей который начинаются с сегодняшней. Пользователь который отправляет запрос должен быть регистратором. """
    )
    @action(detail=True, methods=['get'])
    def get_bookings(self, request, pk=None):
        today = date.today()
        bookings = Booking.objects.filter(queue__branch=pk, date__gte=today)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        operation_summary="Поиск талона по различным реквизитам.",
        operation_description="""
        Эндпоинт для поиска талона по различным реквизитам таким как ФИО, номер телефона, паспорт. Поиск будут идти по тем реквизитам, которые были переданы. Пользователь который отправляет запрос должен быть регистратором."""
    )
    @action(detail=False, methods=['post'])
    def customer_by_props(self, request):
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
    

    @swagger_auto_schema(
        operation_summary="Поиск предварительной записи по различным реквизитам",
        operation_description="""
        Эндпоинт для поиска пред. записей по реквизитам которые были переданы в запрос, таким как ФИО, номер телефона, паспорт. Пользователь который отправляет запрос должен быть регистратором."""
    )
    @action(detail=False, methods=['post'])
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


    @swagger_auto_schema(
        operation_summary="Отменить талон",
        operation_description="""
        Эндпоинт для отмены талона, позиции остальных талонов сдвигаются на 1. Пользователь который отправляет запрос должен быть регистратором."""
    )
    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
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


    @swagger_auto_schema(
        operation_summary="Вписать дополнительную информацию о клиенте",
        operation_description="""
        Эндпоинт для добавления доп. информации о посетителе в поле notes талона. Пользователь который отправляет запрос должен быть регистратором."""
    )
    @action(detail=True, methods=['patch'])
    def write_info(self, request, pk=None):
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