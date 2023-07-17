from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.admins.permissions import IsAdmin
from apps.branches.models import Branch, Cabinet, Floor
from apps.branches.serializers import CabinetSerializer, FloorSerializer
from apps.qsystem.models import Queue, Services
from apps.qsystem.permissions import IsAdmin, IsAdminOfHisBranch
from apps.qsystem.serializers import QueueSerializer

from .models import BaseCalendar, Branch, Calendar, Region, Window
from .serializers import (BaseCalendarSerializer, BranchSerializer,
                          CalendarSerializer, RegionSerializer,
                          WindowSerializer)


class WindowViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Window.objects.all()
    serializer_class = WindowSerializer
    permission_classes = [IsAdmin]


class FloorViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAdmin]


class CabinetViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    permission_classes = [IsAdmin]


class CalendarViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    permission_classes = [IsAdmin]


class BaseCalendarViewSet(ModelViewSet):
    queryset = BaseCalendar.objects.all()
    serializer_class = BaseCalendarSerializer
    permission_classes = [IsAdmin]


""" RegionViewSet является представлением модели Region
 и предоставляет эндпоинт region_branches, 
 который позволяет получить список филиалов, 
 связанных с конкретной областью. """
class RegionViewSet(ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @action(detail=True, methods=['get'])
    def region_branches(self, request, pk=None):
        """ 
        Эндпоинт для получения филиалов находящихся в этой области
        Нужно передать ID области
        """
        region = Region.objects.get(pk=pk)  # Получение объекта области по переданному ID
        branches = region.branches.all()  # Получение всех филиалов, связанных с данной областью
        serializer = BranchSerializer(branches, many=True)  # Сериализация списка филиалов
        return Response(serializer.data, status=200)  # Возврат данных филиалов в виде ответа


""" BranchViewSet представляет модель Branch
 и содержит эндпоинт get_service_types, 
 позволяющий получить список типов услуг, 
 предоставляемых в конкретном филиале. """
class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]


    @action(detail=True, methods=['get'])
    def get_service_types(self, request, pk=None):
        """ 
        Эндпоинт для получения типов услуг в этом филиале
        Нужно передать ID филиала
        """
        branch = Branch.objects.get(pk=pk)  # Получение объекта филиала по переданному ID
        queues = branch.queues.all()  # Получение всех очередей, связанных с данным филиалом
        service_types = set(queue.services.pk for queue in queues)  # Получение типов услуг, связанных с очередями

        return Response({'service_types': list(service_types)}, status=200)  # Возврат списка типов услуг
    
    

""" ServiceQueueAPIView является API-представлением
 и предоставляет эндпоинт get,
 который позволяет получить список услуг (очередей),
 связанных с конкретным филиалом и типом услуги. """
class ServiceQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Эндпоинт для получения всех услуг(очередей) в этом филиале
        Нужно передать ID филиала и ID услуги
        """
        branch_pk = kwargs.get('branch_pk')  # Получение ID филиала из URL
        service_pk = kwargs.get('service_pk')  # Получение ID услуги из URL

        branch = get_object_or_404(Branch, pk=branch_pk)  # Получение объекта филиала по переданному ID
        services = get_object_or_404(Services, pk=service_pk)  # Получение объекта услуги по переданному ID

        queues = Queue.objects.filter(branch=branch, services=services)  # Фильтрация очередей по филиалу и услуге
        serializer = QueueSerializer(queues, many=True)  # Сериализация списка очередей

        return Response(serializer.data, status=200)


