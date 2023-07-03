from django.urls import path, include
from rest_framework import routers
from .views import RegionViewSet, BranchViewSet, ServiceQueueAPIView, WindowViewSet, CalendarViewSet

router = routers.DefaultRouter()
router.register('region', RegionViewSet)
router.register('', BranchViewSet)
router.register('window', WindowViewSet)
router.register('calendar', CalendarViewSet)

urlpatterns = [
    path('branches/', include(router.urls)),
    path('branches/<int:branch_pk>/<int:service_pk>/service_queues/', ServiceQueueAPIView.as_view(), name='service-queues')
]