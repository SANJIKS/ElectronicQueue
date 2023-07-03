from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.qsystem.models import Queue
from .serializers import ChangeMaxCalls, ChangePrintTime




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
    def change_printint_time(self, request, *args, **kwargs):
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
    
