from django.urls import path, include
from rest_framework import routers
from .views import QueueViewSet, CustomerViewSet

router = routers.DefaultRouter()
router.register(r'queues', QueueViewSet)
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]