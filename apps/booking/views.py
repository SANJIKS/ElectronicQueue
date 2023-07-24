from datetime import date
from datetime import datetime

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.db.models import Max
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from decouple import config
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema


User = get_user_model()

from apps.qsystem.models import Customer
from .models import Booking
from .serializers import BookingSerializer, RegisterCustomerSerializer
from apps.branches.models import BaseCalendar, Calendar

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_serializer_class(self):
        if self.action == 'register_customer':
            return RegisterCustomerSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    @swagger_auto_schema(
        operation_summary='Получить все предварительные записи',
        operation_description="""
        Эндпоинт для получения всех предварительных записей"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать предварительную запись',
        operation_description="""
        Эндпоинт для создания предварительной записи, необходимо передать время, дату и очередь на которую записываетесь.
        Пользователь должен быть авторизован.
        Нельзя записаться в нерабочий день, на прошлое время и время в которое филиал не работает. И также нельзя записаться на один день 2 раза.
        Также нельзя записаться если это время уже занято."""
    )
    def create(self, request, *args, **kwargs):
        """
        Эндпоинт для предварительной записи в очередь
        Нужно передь ID очереди, дату и время 
        """
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)

        time = serializer.validated_data.get('time')  # Извлечение времени из валидированных данных
        date_ = serializer.validated_data.get('date')  # Извлечение даты из валидированных данных
        queue = serializer.validated_data.get('queue')  # Извлечение очереди из валидированных данных

        branch = queue.branch

        if queue.is_blocked:
            return Response({'error': 'В данный момент очередь недоступна!'}, status=400)

        base_holiday = BaseCalendar.objects.filter(date=date_)
        if base_holiday.exists():
            return Response({'error': 'В этот день филиалы не работают!'}, status=400)

        holiday = Calendar.objects.filter(branch=branch, date=date_)
        if holiday.exists():
            return Response({'error': 'В этот день филиал не работает!'}, status=400)


        if not time or time < branch.schedule_start or time > branch.schedule_end: # Проверка, что выбранное время находится в рабочем расписании филиала
            return Response(
                {'error': 'Неверное время или филиал не работает в это время'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        user_bookings = Booking.objects.filter(user=user, date=date_).exists() # Проверка наличия бронирований пользователя на выбранную дату

        if user_bookings: # Если у пользователя уже есть бронирование на выбранную дату
            return Response(
                {'error': 'Вы уже записывались в этот день!'}
            )
        
        existing_booking = Booking.objects.filter(time=time, date=date_).exists() # Проверка на наличие брони на ту же дату и время

        if existing_booking:
            return Response(
                {'error': 'Это время занято!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_date = date.today()
        current_time = datetime.now().time()
        if date_ < current_date or (date_ == current_date and time < current_time): # Проверка, что выбранная дата и время не являются прошлыми
            return Response(
                {'error': 'Вы не можете записаться на прошедшую дату или время!'},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) # Возврат успешного ответа с данными бронирования
    

    def get_all_tickets(self, queue):
        return Customer.objects.filter(queue=queue) # Получение всех талонов для определенной очереди

    
    """ Метод, который представляет эндпоинт для печати талона по предварительной записи
     и создания талона с данными этой записи """
    @swagger_auto_schema(
        operation_summary='Распечатать и создать талон по предварительной записи',
        operation_description="""
        Эндпоинт для создания талона по пред. записи, время и дата пред. записи будут установлены на талоне.
        Вернется также эндпоинт для печати талона.
        Нельзя распечатать талон если он просрочен (дата записи уже прошла).
        Распечатать можно только в день записи

        Чтобы распечатать необходимо ввести пин-код который был выдан при создании предварительной записи"""
    )
    @action(detail=False, methods=['post'])
    def register_customer(self, request):
        pin = request.data.get('pin')  # Извлечение пин-кода талона из запроса

        matching_booking = Booking.objects.filter(
        pin=pin,
        ).first()  # Поиск бронирования, соответствующего переданным данным
        
        if not matching_booking: # Если бронирование не найдено
            return Response({'error': 'Запись не найдена.'}, status=400)

        if matching_booking.is_registered: # Если талон уже был распечатан
            return Response({'message': 'Талон уже был распечатан!'}, status=400) 
        
        current_date = date.today()
        current_time = datetime.now().time()
        
        # # При попытке распечатать талон прошедшего времени записи
        if matching_booking.date < current_date or (matching_booking.date == current_date and matching_booking.time < current_time):
            return Response({'error': 'Нельзя распечатать просроченный талон!'}, status=400)    
        
        # При попытке распечатать талон раньше дня записи
        elif matching_booking.date > current_date:
            return Response({'error': 'Сегодня нельзя распечатать этот талон!'}, status=400)
        
        queue = matching_booking.queue # Получение очереди из найденного бронирования

        # Формирование номера талона
        all_tickets = self.get_all_tickets(queue)
        max_ticket_number = all_tickets.aggregate(Max('ticket_number'))
        last_ticket_number = max_ticket_number.get('ticket_number__max')

        if last_ticket_number is not None:
            max_ticket_number = int(last_ticket_number[1:]) + 1
        else:
            max_ticket_number = 1

        ticket_number = f"{queue.symbol}{max_ticket_number:02d}"


        customer = Customer.objects.create(
            queue=matching_booking.queue,
            time=matching_booking.time,
            category='booked',
            ticket_number=ticket_number,
            position=0
        ) # Создание объекта Customer 

        customer.save() # Сохранение объекта Customer в базе данных

        matching_booking.is_registered = True # Установка флага "is_registered" в True для бронирования
        matching_booking.save() # Сохранение изменений в бронировании

        customer_id = customer.id # Получение идентификатора печатного талона

        redirect_url = config("BASE_URL")+reverse('printing-detail', args=[customer_id]) # Формирование URL для печати талона

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ticket_broadcast",
            {
                "type": "send_ticket_list",
                "event": {}  
            }
        )


        return Response({'message': 'Талон успешно выдан!', 'customer_id': customer_id, 'redirect_url': redirect_url}, status=200)
    

    @swagger_auto_schema(
        operation_summary='Retrieve чтение предварительной записи',
        operation_description="""
        Эндпоинт для получения предварительной записи по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить предварительную запись',
        operation_description="""
        Эндпоинт для обновления предварительной записи"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить предварительную запись партийно',
        operation_description="""
        Эндпоинт для партийного обновления предварительной записи"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить предварительную запись',
        operation_description="""
        Эндпоинт для удаления предварительной записи"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

