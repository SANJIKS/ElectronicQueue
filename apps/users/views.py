from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.qsystem.models import Customer
from apps.qsystem.serializers import CustomerSerializer
from apps.reports.models import OperatorAction

from .models import Profile
from .serializers import ProfileSerializer


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
        Эндпоинт для получения истории талонов
        Необходимо передать ФИО
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        surname = request.data.get('surname')
        tickets = Customer.objects.filter(first_name=first_name, last_name=last_name, surname=surname)  # Получение всех талонов пользователя

        serializer = CustomerSerializer(tickets, many=True)  
        return Response(serializer.data)
    

class OperatorProfileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def come_in_system(self, request):
        operator = self.request.user
        OperatorAction.objects.create(operator=operator, action='come', event='Оператор вошел в систему')
        return Response({'message': 'Протокол создан'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def out_of_system(self, request):
        operator = self.request.user
        OperatorAction.objects.create(operator=operator, action='out', event='Оператор вышел из системы')
        return Response({'message': 'Протокол создан'}, status=status.HTTP_200_OK)
    