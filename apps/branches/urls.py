from django.urls import path, include
from rest_framework import routers
from .views import RegionViewSet, BranchViewSet, ServiceQueueAPIView, WindowViewSet, CalendarViewSet, BaseCalendarViewSet, FloorViewSet, CabinetViewSet

router = routers.DefaultRouter()
router.register('branches/region', RegionViewSet)
router.register('branch/window', WindowViewSet)
router.register('branch/calendar', CalendarViewSet)
router.register('branches/basecalendar', BaseCalendarViewSet)
router.register('branch/floor', FloorViewSet)
router.register('branch/cabinet', CabinetViewSet)
router.register('branches', BranchViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('branch/<int:branch_pk>/<int:service_pk>/service_queues/', ServiceQueueAPIView.as_view(), name='service-queues')
]
