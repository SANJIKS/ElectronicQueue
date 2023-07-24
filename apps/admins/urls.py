from django.urls import path, include
from rest_framework import routers
from .views import AdminViewSet, TCPConfigView, UserViewSet, UsersProfileViewSet, BackupViewSet, ProtocolView

router = routers.DefaultRouter()
router.register('', AdminViewSet, basename='admins')
router.register('users', UserViewSet, basename='users')
router.register('backups', BackupViewSet, basename='backups')
router.register('protocol', ProtocolView, basename='protocol')

urlpatterns = [
    path('', include(router.urls)),
    path('tcp-config/', TCPConfigView.as_view(), name='tcp-config'),
    path('profile/', UsersProfileViewSet.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
    path('profile/<int:pk>', UsersProfileViewSet.as_view({'patch': 'update_profile'}), name='update_profile'),
    path('get_retrieve/<int:pk>', UsersProfileViewSet.as_view({'get': 'get_retrieve'}), name='get_retrieve'),
]