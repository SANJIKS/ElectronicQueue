from datetime import date
from datetime import datetime

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.utils import timezone
from django.db.models import Max
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from decouple import config
from django.urls import reverse


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
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        surname = serializer.validated_data.get('surname')

        branch = queue.branch

        if queue.is_blocked == True:
            return Response({'error': 'В данный момент очередь недоступна!'}, status=400)

        base_holiday = BaseCalendar.objects.filter(date=date_)
        if base_holiday.exists():
            return Response({'error': 'В этот день филиалы не работают!'}, status=400)

        holiday = Calendar.objects.filter(branch=branch, date=date_)
        if holiday.exists():
            return Response({'error': 'В этот день филиал не работает!'}, status=400)


        user_bookings = Booking.objects.filter(first_name=first_name, last_name=last_name, surname=surname, date=date_).exists() # Проверка наличия бронирований пользователя на выбранную дату

        if time < branch.schedule_start or time > branch.schedule_end: # Проверка, что выбранное время находится в рабочем расписании филиала
            return Response(
                {'error': 'Филиал не работает в это время.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        
        # user = self.request.user
        # if user.profile.first_name == None or user.profile.last_name == None or user.profile.surname == None: # Проверка, что у пользователя заполнены данные в профиле
        #     return Response({'error': 'Заполните данные своего профиля!'}, status=400)
        
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) # Возврат успешного ответа с данными бронирования
    

    def get_all_tickets(self, queue):
        return Customer.objects.filter(queue=queue) # Получение всех талонов для определенной очереди

    
    """ Метод, который представляет эндпоинт для печати талона по предварительной записи
     и создания талона с данными этой записи """
    @action(detail=False, methods=['post'])
    def register_customer(self, request):
        """
        Эндпоинт для печати талона по предварительной записи
        Нужно передать ФИО и пин-код талона
        """
        first_name = request.data.get('first_name')  # Извлечение имени из запроса
        last_name = request.data.get('last_name')  # Извлечение фамилии из запроса
        surname = request.data.get('surname')  # Извлечение отчества из запроса
        pin = request.data.get('pin')  # Извлечение пин-кода талона из запроса


        matching_booking = Booking.objects.filter(
        pin=pin,
        first_name=first_name,
        last_name=last_name,
        surname=surname
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
            # user=matching_booking.user,
            time=matching_booking.time,
            category='booked',
            ticket_number=ticket_number,
            first_name=first_name,
            last_name=last_name,
            surname=surname,
            pasport=matching_booking.pasport,
            phone_number=matching_booking.phone_number,
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
                "event": {}  # Передаем пустой объект в качестве аргумента event
            }
        )


        return Response({'message': 'Талон успешно выдан!', 'customer_id': customer_id, 'redirect_url': redirect_url}, status=200)
