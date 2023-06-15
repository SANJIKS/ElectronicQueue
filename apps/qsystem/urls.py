from django.urls import path, include
from rest_framework import routers
from .views import QueueViewSet, CustomerViewSet, PrintTicket

router = routers.DefaultRouter()
router.register(r'queues', QueueViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'printing', PrintTicket, basename='printing')

urlpatterns = [
    path('', include(router.urls)),
]