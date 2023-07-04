from django.urls import path, include
from rest_framework import routers
from .views import AdminViewSet, TCPConfigView

router = routers.DefaultRouter()
router.register('', AdminViewSet, basename='admins')

urlpatterns = [
    path('', include(router.urls)),
    path('tcp-config/', TCPConfigView.as_view(), name='tcp-config'),
]