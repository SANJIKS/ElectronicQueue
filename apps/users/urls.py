from django.urls import path, include
from rest_framework import routers
from .views import ProfileView, OperatorViewSet

router = routers.DefaultRouter()
router.register(r'', OperatorViewSet, basename='operator')


urlpatterns = [
    path('operator/', include(router.urls)),
    path('profile/', ProfileView.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
    path('profile/user_history/', ProfileView.as_view({'get': 'user_history'}), name='user_history'),
]