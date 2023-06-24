from django.urls import path, include
from rest_framework import routers
from .views import QueueViewSet, CustomerViewSet, PrintTicket

router = routers.DefaultRouter()
# router.register(r'queues', QueueViewSet, basename='queue')
router.register(r'', CustomerViewSet, basename='customer')
router.register(r'printing', PrintTicket, basename='printing')

queue_list = QueueViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

queue_detail = QueueViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('customers/', include(router.urls)),
    path('queues/', queue_list),
    path('queues/<int:pk>/', queue_detail),
]