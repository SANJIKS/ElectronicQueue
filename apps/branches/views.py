from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .serializers import RegionSerializer, BranchSerializer
from .models import Region, Branch, Window
from apps.qsystem.models import Queue, Services
from apps.qsystem.serializers import QueueSerializer


class RegionViewSet(ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @action(detail=True, methods=['get'])
    def region_branches(self, request, pk=None):
        region = Region.objects.get(pk=pk)
        branches = region.branches.all()
        serializer = BranchSerializer(branches, many=True)
        return Response(serializer.data, status=200)


class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    @action(detail=True, methods=['get'])
    def get_service_types(self, request, pk=None):
        branch = Branch.objects.get(pk=pk)
        queues = branch.queues.all()  
        service_types = set(queue.services.pk for queue in queues)

        return Response({'service_types': list(service_types)}, status=200)
    
    


class ServiceQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        branch_pk = kwargs.get('branch_pk')
        service_pk = kwargs.get('service_pk')

        branch = get_object_or_404(Branch, pk=branch_pk)
        services = get_object_or_404(Services, pk=service_pk)

        queues = Queue.objects.filter(branch=branch, services=services)
        serializer = QueueSerializer(queues, many=True)

        return Response(serializer.data, status=200)