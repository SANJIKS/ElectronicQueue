from django.urls import path, include
from rest_framework import routers
from .views import ProfileView, OperatorProfileViewSet

router = routers.DefaultRouter()
router.register(r'operator', OperatorProfileViewSet, basename='operator')

urlpatterns = [
    path('', include(router.urls)),
    path('', ProfileView.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
    path('user_history/', ProfileView.as_view({'get': 'user_history'}), name='user_history'),
    path('get_retrieve/<int:pk>', ProfileView.as_view({'get': 'get_retrieve'}), name='get_retrieve')
]
