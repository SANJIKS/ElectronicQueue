from django.urls import path, include
from rest_framework import routers
from .views import ProfileView, OperatorProfileViewSet

router = routers.DefaultRouter()
router.register(r'operator', OperatorProfileViewSet, basename='operator')

urlpatterns = [
    path('profile/', include(router.urls)),
    path('profile/', ProfileView.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
    path('profile/user_history/', ProfileView.as_view({'get': 'user_history'}), name='user_history'),
]
