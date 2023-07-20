import os
from datetime import datetime
from pytz import timezone as timez
import subprocess

from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.core.management import call_command
from django.conf import settings

from apps.admins.permissions import IsAdmin
from apps.qsystem.models import Queue
from apps.users.models import Profile
from apps.users.serializers import ProfileSerializer
from apps.branches.models import Branch

from apps.report_apps.operator_reports.models import OperatorAction
from apps.report_apps.customer_reports.models import CustomerAction
from apps.report_apps.operator_reports.serializers import OperatorActionSerializer
from apps.report_apps.customer_reports.serializers import CustomerActionSerializer
from .serializers import (ChangeMaxCalls,
                          ChangeMaxTransfers, ChangePrintTime,
                          ChangeWaitingTime, GetOnlineWindows)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    

class UsersProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    
    def get_permissions(self):
        if self.action == 'get':
            return [IsAuthenticated()]
        return super().get_permissions()

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
    

    @action(detail=True, methods=['get'])
    def get_retrieve(self, request, pk=None):
        profile = Profile.objects.get(pk=pk)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)


class AdminViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(request_body=ChangeMaxCalls)
    def change_max_calls(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        number = request.data.get('number')
        queue.max_calls = number
        queue.save()
        return Response(status=status.HTTP_200_OK)
    

    @action(detail=True, methods=['post'])
    @swagger_auto_schema(request_body=ChangePrintTime)
    def change_printing_time(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        start = request.data.get('start')
        end = request.data.get('end')
        queue.print_start = start
        queue.print_end = end
        queue.save()
        return Response(status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['post'])
    def block_queues(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        if queue.is_blocked == True:
            queue.is_blocked = False
            queue.save()
            return Response({'message': 'Очередь разблокирована'}, status=200)
        queue.is_blocked = True
        queue.save()
        return Response({'message': 'Очередь заблокирована'}, status=200)
    

    @swagger_auto_schema(request_body=ChangeWaitingTime)
    @action(detail=True, methods=['post'])
    def change_operator_waiting_time(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        time = request.data.get('time')
        queue.waiting_time_operator = time
        queue.save()
        return Response({'message': 'Время изменено'}, status=200)
    

    @swagger_auto_schema(request_body=ChangeMaxTransfers)
    @action(detail=True, methods=['post'])
    def change_max_transfers(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        number = request.data.get('number')
        queue.max_calls = number
        queue.save()
        return Response({'message': 'Максимальное количество вызовов изменено!'})
    

    @action(detail=True, methods=['post'])
    def change_auto_transfer(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        queue = Queue.objects.get(pk=pk)
        if queue.auto_transfer:
            queue.auto_transfer = False
            queue.save()
            return Response({'message': 'Автоматический перенос в конец очереди отключен'})
        queue.auto_transfer = True
        queue.save()
        return Response({'message': 'Автоматический перенос в конец очереди включен'})


    @action(detail=False, methods=['get'])
    def get_online_operators(self, request, *args, **kwargs):
        admin = self.request.user
        branch = Branch.objects.get(admin=admin)
        operators = User.objects.filter(profile__position='operator', queues__branch=branch, window__is_online=True)

        serializer = GetOnlineWindows(operators, many=True)
        return Response(serializer.data, status=200)


class TCPConfigView(APIView):
    def get(self, request):
        return Response({"tcp_port": settings.TCP_PORT})

    def put(self, request):
        tcp_port = request.data.get("tcp_port")
        if tcp_port:
            settings.TCP_PORT = tcp_port
            return Response({"message": "TCP port updated successfully."})
        else:
            return Response({"error": "TCP port not provided."}, status=400)


class BackupViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'backup_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['backup_name']
        ),
        operation_summary="Create database backup",
        operation_description="Create a backup of the current database.",
        responses={
            200: "Backup created successfully",
            400: "Invalid request body",
        }
    )
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        backup_name = request.data.get('backup_name')
        if not backup_name:
            return Response({'error': 'Backup name is required'}, status=400)

        backup_name = backup_name + '.psql.bin'
        backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_name)

        if os.path.isfile(backup_path):
            return Response({'error': 'Backup file already exists'}, status=409)

        try:
            call_command('dbbackup', output_filename=backup_path)
            return Response({'message': 'Backup created successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'backup_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['backup_name']
        ),
        operation_summary="Restore database backup",
        operation_description="Restore the database from a backup.",
        responses={
            200: "Database restored successfully",
            400: "Invalid request body",
            500: "Internal server error"
        }
    )
    @action(detail=False, methods=['post'])
    def restore_backup(self, request):
        backup_name = request.data.get('backup_name')
        if not backup_name:
            return Response({'error': 'Backup name is required'}, status=400)

        backup_name = backup_name + '.psql.bin'
        backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_name)
        if not os.path.isfile(backup_path):
            return Response({'error': 'Backup file does not exist'}, status=400)

        try:
            call_command('dbrestore', input_filename=backup_path, interactive=False)
            return Response({'message': 'Database restored successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)        
    
    @action(detail=False, methods=['get'])
    def get_backups(self, request):
        backups = os.listdir('backups')
        return Response(backups, status=status.HTTP_200_OK)


class ProtocolView(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def get_operator_actions(self, request):
        admin = self.request.user
        branch = Branch.objects.get(admin=admin)
        today = datetime.now().astimezone(timez('Asia/Bishkek'))

        actions = set(OperatorAction.objects.filter(operator__queues__branch=branch, created_at__date=today))
        serializer = OperatorActionSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['get'])
    def get_customer_actions(self, request):
        admin = self.request.user
        branch = Branch.objects.get(admin=admin)
        today = datetime.now().astimezone(timez('Asia/Bishkek'))

        actions = set(CustomerAction.objects.filter(customer__queue__branch=branch, created_at__date=today))
        serializer = CustomerActionSerializer(actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
