from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer

from apps.branches.models import Floor, Cabinet
from apps.branches.serializers import CabinetSerializer, FloorSerializer
from apps.admins.permissions import IsAdmin
from apps.qsystem.models import Queue
from apps.users.models import Profile
from apps.users.serializers import ProfileSerializer
from .serializers import ChangeMaxCalls, ChangeMaxTransfers, ChangePrintTime, ChangeWaitingTime

User = get_user_model()

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAdmin]


class CabinetViewSet(viewsets.ModelViewSet):
    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    permission_classes = [IsAdmin]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    

class UsersProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    
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
    


from rest_framework.views import APIView
from django.conf import settings

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
