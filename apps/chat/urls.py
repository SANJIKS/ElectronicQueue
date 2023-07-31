from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PrivateChatViewSet, PrivateMessageViewSet

router = DefaultRouter()
router.register(r'private_chat', PrivateChatViewSet, basename='private_chat')
router.register(r'private_message', PrivateMessageViewSet, basename='private_message')

urlpatterns = [
    path('', include(router.urls)),
]
