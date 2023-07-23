from django.urls import path, include, re_path
from rest_framework import routers
from .views import ProfileView, OperatorProfileViewSet, CustomTokenObtainPairView, CustomTokenRefreshView, CustomTokenVerifyView, CustomUserViewSet

router = routers.DefaultRouter()
router.register(r'operator', OperatorProfileViewSet, basename='operator')


urlpatterns = [
    path('users/<int:pk>/', CustomUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-detail'),
    path('users/', CustomUserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('users/activation/', CustomUserViewSet.as_view({'post': 'activation'}), name='user-activation'),
    path('users/resend_activation/', CustomUserViewSet.as_view({'post': 'resend_activation'}), name='user-resend-activation'),
    path('users/set_password/', CustomUserViewSet.as_view({'post': 'set_password'}), name='user-set-password'),
    path('users/reset_password/', CustomUserViewSet.as_view({'post': 'reset_password'}), name='user-reset-password'),
    path('users/reset_password_confirm/', CustomUserViewSet.as_view({'post': 'reset_password_confirm'}), name='user-reset-password-confirm'),
    path('users/set_username/', CustomUserViewSet.as_view({'post': 'set_username'}), name='user-set-username'),
    path('users/reset_username/', CustomUserViewSet.as_view({'post': 'reset_username'}), name='user-reset-username'),
    path('users/reset_username_confirm/', CustomUserViewSet.as_view({'post': 'reset_username_confirm'}), name='user-reset-username-confirm'),
    path('users/me/', CustomUserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me', 'delete': 'me'}), name='user-me'),
    
    
    path('login/jwt/create/', CustomTokenObtainPairView.as_view(), name="jwt-create"),
    path('login/jwt/refresh/', CustomTokenRefreshView.as_view(), name="jwt-refresh"),
    path('login/jwt/verify/', CustomTokenVerifyView.as_view(), name="jwt-verify"),
    path('profile/', include(router.urls)),
    path('profile/', ProfileView.as_view({'get': 'get', 'put': 'put', 'patch': 'patch'}), name='profile'),
    path('profile/user_history/', ProfileView.as_view({'get': 'user_history'}), name='user_history'),
    path('profile/get_retrieve/<int:pk>', ProfileView.as_view({'get': 'get_retrieve'}), name='get_retrieve'),
]
