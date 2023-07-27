from django.urls import path, include
from rest_framework import routers
from .views import QueueViewSet, CustomerViewSet, PrintingView, voice_bot

router = routers.DefaultRouter()
# router.register(r'queues', QueueViewSet, basename='queue')
router.register(r'', CustomerViewSet, basename='customer')
router.register(r'printing', PrintingView, basename='printing')

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
     path('ticket_dictor/', voice_bot),
    path('queues/', queue_list),
    path('customers/', include(router.urls)),
    path('queues/<int:pk>/', queue_detail),
    path('queues/<int:pk>/get_documents/', QueueViewSet.as_view({'get': 'get_documents'}), name='get_documents'),
]
