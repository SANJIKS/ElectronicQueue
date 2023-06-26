from django.urls import path, include
from rest_framework import routers
from .views import RegionViewSet, BranchViewSet, ServiceQueueAPIView

router = routers.DefaultRouter()
router.register('region', RegionViewSet)
router.register('', BranchViewSet)

urlpatterns = [
    path('branches/', include(router.urls)),
    path('branches/<int:branch_pk>/<int:service_pk>/service_queues/', ServiceQueueAPIView.as_view(), name='service-queues')
]