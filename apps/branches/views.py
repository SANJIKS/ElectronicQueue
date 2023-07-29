from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from drf_yasg.utils import swagger_auto_schema

from apps.admins.permissions import IsAdmin
from apps.branches.models import Branch, Cabinet, Floor
from apps.branches.serializers import CabinetSerializer, FloorSerializer
from apps.qsystem.models import Queue, Services
from apps.qsystem.permissions import IsAdmin, IsAdminOfHisBranch
from apps.qsystem.serializers import QueueSerializer

from .models import BaseCalendar, Branch, Calendar, Region, Window, Board, Ad
from .serializers import (BaseCalendarSerializer, BranchSerializer,
                          CalendarSerializer, RegionSerializer, ServiceSerializer,
                          WindowSerializer, BoardSerializer, AdSerializer)


class AdViewSet(ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer

    @swagger_auto_schema(
        operation_summary='Получить всю рекламу',
        operation_description="""
        Эндпоинт для получения всех реклам"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить рекламу',
        operation_description="""
        Эндпоинт для добавления рекламы, видео/фото"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Получить рекламу',
        operation_description="""
        Эндпоинт для получения рекламы по id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить рекламу',
        operation_description="""
        Эндпоинт для обновления рекламы"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить рекламу партийно',
        operation_description="""
        Эндпоинт для партийного обновления рекламы"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить рекламу',
        operation_description="""
        Эндпоинт для удаления рекламы"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class BoardViewSet(ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    @swagger_auto_schema(
        operation_summary='Получить всю рекламу одного табла',
        operation_description="""
        Эндпоинт для получения всей рекламу пренадлежащей этому таблу, необходимо передать id табла"""
    )
    @action(detail=True, methods=['GET'])
    def ads(self, request, pk=None):
        board = self.get_object()
        ads = board.ads.all()
        serializer = AdSerializer(ads, many=True)
        return Response(serializer.data)
    

    @swagger_auto_schema(
    operation_summary='Получить все окна-табло по id филиала',
    operation_description="""
    Эндпоинт для получения всех окон-табло, пренадлежащих данному филиалу, необходимо передать id филиала"""
    )
    @action(detail=True, methods=['GET'])
    def boards(self, request, pk=None):
        billboards = Board.objects.filter(branch=pk)
        serializer = BoardSerializer(billboards, many=True)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        operation_summary='Получить все табло',
        operation_description="""
        Эндпоинт для получения всех табл"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить табло',
        operation_description="""
        Эндпоинт для создания табла"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_summary='Retrieve табло',
        operation_description="""
        Эндпоинт для получения табла по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить табло',
        operation_description="""
        Эндпоинт для обновления табла"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить табло партийно',
        operation_description="""
        Эндпоинт для партийного обновления табла"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить табло',
        operation_description="""
        Эндпоинт для удаления табла"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class WindowViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Window.objects.all()
    serializer_class = WindowSerializer
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary='Получить все окна',
        operation_description="""
        Эндпоинт для получения всех окон"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать окно  (Для администатора)',
        operation_description="""
        Эндпоинт для создания окна"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Получить окно по его id  (Для администатора)',
        operation_description="""
        Эндпоинт для retrieve чтения окон"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить окно  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления окон"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить окно партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления окон"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить окно  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления окон"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class FloorViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary='Получить все этажи',
        operation_description="""
        Эндпоинт для получения всех этажей"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить этажи  (Для администатора)',
        operation_description="""
        Эндпоинт для создания этажей филиала"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтения этажей  (Для администатора)',
        operation_description="""
        Эндпоинт для получения этажа по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить этажи  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления этажей филиала"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить этажи партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления этажей филиала"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить этажи  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления этажей филиала"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CabinetViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary='Получить все кабинеты',
        operation_description="""
        Эндпоинт для получения всех кабинетов"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Создать кабинет  (Для администатора)',
        operation_description="""
        Эндпоинт для создания кабинета филиала"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтение кабинета  (Для администатора)',
        operation_description="""
        Эндпоинт для получения кабинета филиала по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить кабинет  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления кабинета филиала"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить кабинет партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления кабинета филиала"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить кабинет  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления кабинета филиала  (Для администатора)"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CalendarViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update', 'put', 'delete']:
            return [IsAdmin(),IsAdminOfHisBranch()]
        else:
            return [IsAdmin()]

    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary='Получить все календари',
        operation_description="""
        Эндпоинт для получения всех календарей филиалов"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить нерабочий день  (Для администатора)',
        operation_description="""
        Эндпоинт для добавления даты, в который филиал не будет работать"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтение дней  (Для администатора)',
        operation_description="""
        Эндпоинт для получения нерабочих дней по их id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить нерабочий день  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления данных нерабочей даты филиала"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить нерабочий день партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления данных нерабочей даты филиала"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить нерабочую дату  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления нерабочего дня филиала"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class BaseCalendarViewSet(ModelViewSet):
    queryset = BaseCalendar.objects.all()
    serializer_class = BaseCalendarSerializer
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary='Получить все общие календари',
        operation_description="""
        Эндпоинт для получения всех общих календарей"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить нерабочий день для всех филиалов  (Для администатора)',
        operation_description="""
        Эндпоинт для создания даты в который все филиалы не работают"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтение нерабочей даты  (Для администатора)',
        operation_description="""
        Эндпоинт для получения нерабочего дня по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить нерабочий день для всех филиалов  (Для администатора)',
        operation_description="""
        Энпоинт для обновления данных нерабочей даты для всех филиалов"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить нерабочий день для всех филиалов партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления нерабочей даты для всех филиалов"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить нерабочий день для всех филиалов  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления нерабочей даты для всех филиалов"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


""" RegionViewSet является представлением модели Region
 и предоставляет эндпоинт region_branches, 
 который позволяет получить список филиалов, 
 связанных с конкретной областью. """
class RegionViewSet(ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


    @swagger_auto_schema(
        operation_summary='Получить филиалы по области',
        operation_description="""
        Эндпоинт для получения списка филиалов находящихся в данной области, необходимо передать id области"""
    )
    @action(detail=True, methods=['get'])
    def region_branches(self, request, pk=None):
        region = Region.objects.get(pk=pk)  # Получение объекта области по переданному ID
        branches = region.branches.all()  # Получение всех филиалов, связанных с данной областью
        serializer = BranchSerializer(branches, many=True)  # Сериализация списка филиалов
        return Response(serializer.data, status=200)  # Возврат данных филиалов в виде ответа
            
    @swagger_auto_schema(
        operation_summary='Получить все области',
        operation_description="""
        Эндпоинт для получения всех областей"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить область  (Для администатора)',
        operation_description="""
        Эндпоинт для создания области"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтение области  (Для администатора)',
        operation_description="""
        Эндпоинт для получения области по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить область  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления области"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить область партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления области"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить область  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления области"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)




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
        elif self.action == 'create':
            return [IsAdmin()]
        else:
            return [AllowAny()]
    
    
    @swagger_auto_schema(
        operation_summary='Получить типы услуг доступных в филиале',
        operation_description="""
        Эндпоинт для получения всех типов услуг которые обслуживаются в данном филиале.
        Необходимо передать id филиала"""
    )
    @action(detail=True, methods=['get'])
    def get_service_types(self, request, pk=None):
        branch = Branch.objects.get(pk=pk)  # Получение объекта филиала по переданному ID
        queues = branch.queues.all()  # Получение всех очередей, связанных с данным филиалом
        service_types = set(queue.services for queue in queues)  # Получение типов услуг, связанных с очередями
        serializer = ServiceSerializer(list(service_types), many=True)

        return Response(serializer.data, status=200)  # Возврат списка типов услуг

    @swagger_auto_schema(
        operation_summary='Получить все филиалы',
        operation_description="""
        Эндпоинт для получения всех филиалов"""
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Добавить филиал  (Для администатора)',
        operation_description="""
        Эндпоинт для создания филиала"""
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Retrieve чтение филиала  (Для администатора)',
        operation_description="""
        Эндпоинт для получения филиала по его id"""
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить филиал  (Для администатора)',
        operation_description="""
        Эндпоинт для обновления филиала"""
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Обновить филиал партийно  (Для администатора)',
        operation_description="""
        Эндпоинт для партийного обновления филиала"""
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary='Удалить филиал  (Для администатора)',
        operation_description="""
        Эндпоинт для удаления филиала"""
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    

class ServiceQueueAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='Получить все очереди(услуги) по id филиала и типа услуги',
        operation_description="""
        Эндпоинт для получения списка очередей(услуг), очереди отфильтрованы по филиалу и типу услуги. 
        Необходимо передать id услуги и id филиала"""
    )
    def get(self, request, *args, **kwargs):
        branch_pk = kwargs.get('branch_pk')  # Получение ID филиала из URL
        service_pk = kwargs.get('service_pk')  # Получение ID услуги из URL

        branch = get_object_or_404(Branch, pk=branch_pk)  # Получение объекта филиала по переданному ID
        services = get_object_or_404(Services, pk=service_pk)  # Получение объекта услуги по переданному ID

        queues = Queue.objects.filter(branch=branch, services=services)  # Фильтрация очередей по филиалу и услуге
        serializer = QueueSerializer(queues, many=True)  # Сериализация списка очередей

        return Response(serializer.data, status=200)


