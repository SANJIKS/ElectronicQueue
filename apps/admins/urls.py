from django.urls import path, include
from rest_framework import routers
from .views import AdminViewSet, TCPConfigView, UserViewSet, UsersProfileViewSet, FloorViewSet, CabinetViewSet

router = routers.DefaultRouter()
router.register('', AdminViewSet, basename='admins')
router.register('users', UserViewSet, basename='users')
router.register('floors', FloorViewSet, basename='floors')
router.register('cabinets', CabinetViewSet, basename='cabinets')

urlpatterns = [
    path('', include(router.urls)),
    path('tcp-config/', TCPConfigView.as_view(), name='tcp-config'),
    path('profile/', UsersProfileViewSet.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
]