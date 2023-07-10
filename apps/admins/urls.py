from django.urls import path, include
from rest_framework import routers
from .views import AdminViewSet, TCPConfigView, UserViewSet, UsersProfileViewSet, FloorViewSet, CabinetViewSet, BackupViewSet, ProtocolView

router = routers.DefaultRouter()
router.register('', AdminViewSet, basename='admins')
router.register('users', UserViewSet, basename='users')
router.register('floors', FloorViewSet, basename='floors')
router.register('cabinets', CabinetViewSet, basename='cabinets')
router.register('backups', BackupViewSet, basename='backups')
router.register('protocol', ProtocolView, basename='protocol')

urlpatterns = [
    path('', include(router.urls)),
    path('tcp-config/', TCPConfigView.as_view(), name='tcp-config'),
    path('profile/', UsersProfileViewSet.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
]