from datetime import date
from datetime import datetime

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
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)

        time = serializer.validated_data.get('time')
        date_ = serializer.validated_data.get('date')
        queue = serializer.validated_data.get('queue')

        user_bookings = Booking.objects.filter(user=request.user, date=date_).exists()

        branch = queue.branch
        if time < branch.schedule_start or time > branch.schedule_end:
            return Response(
                {'error': 'Филиал не работает в это время.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_bookings:
            return Response(
                {'error': 'Вы уже записывались в этот день!'}
            )
        
        existing_booking = Booking.objects.filter(time=time, date=date_).exists()

        if existing_booking:
            return Response(
                {'error': 'Это время занято!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_date = date.today()
        current_time = datetime.now().time()
        if date_ < current_date or (date_ == current_date and time < current_time):
            return Response(
                {'error': 'Вы не можете записаться на прошедшую дату или время!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        if user.profile.first_name == None or user.profile.last_name == None or user.profile.surname == None:
            return Response({'error': 'Заполните данные своего профиля!'}, status=400)
        
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

    def get_all_tickets(self, queue):
        return Customer.objects.filter(queue=queue)


    @action(detail=False, methods=['post'])
    def register_customer(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        surname = request.data.get('surname')
        pin = request.data.get('pin')


        matching_booking = Booking.objects.filter(pin=pin, user__profile__first_name=first_name, user__profile__last_name=last_name, user__profile__surname=surname).first()
        
        if not matching_booking:
            return Response({'error': 'Запись не найдена.'}, status=400)

        if matching_booking.is_registered:
            return Response({'message': 'Талон уже был распечатан!'}, status=400) 
        
        current_date = date.today()
        current_time = datetime.now().time()
        
        if matching_booking.date < current_date or (matching_booking.date == current_date and matching_booking.time < current_time):
            return Response({'error': 'Нельзя распечатать просроченный талон!'}, status=400)    
        
        elif matching_booking.date > current_date:
            return Response({'error': 'Сегодня нельзя распечатать этот талон!'}, status=400)
        
        queue = matching_booking.queue
    
        all_tickets = self.get_all_tickets(queue)
        max_ticket_number = all_tickets.aggregate(Max('ticket_number'))
        last_ticket_number = max_ticket_number.get('ticket_number__max')

        if last_ticket_number is not None:
            max_ticket_number = int(last_ticket_number[1:]) + 1
        else:
            max_ticket_number = 1

        ticket_number = f"{queue.symbol}{max_ticket_number:02d}"

        # position = all_tickets.aggregate(Max('position'))
        # last_position = position.get('position__max')

        # if last_position is not None:
        #     position = last_position + 1
        # else:
        #     position = 1


        customer = Customer.objects.create(
            queue=matching_booking.queue,
            user=matching_booking.user,
            time=matching_booking.time,
            category='booked',
            ticket_number=ticket_number,
            position=0
        )

        customer.save()

        matching_booking.is_registered = True
        matching_booking.save()

        customer_id = customer.id

        redirect_url = config("BASE_URL")+reverse('printing-detail', args=[customer_id])  


        return Response({'message': 'Талон успешно выдан!', 'customer_id': customer_id, 'redirect_url': redirect_url}, status=200)
