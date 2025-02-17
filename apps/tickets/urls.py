from django.urls import path, include
from rest_framework import routers
from .views import OperatorViewSet, OperatorGetViewSet, RegistratorViewSet

router = routers.DefaultRouter()
router.register(r'operator', OperatorViewSet, basename='operator')
router.register(r'operator', OperatorGetViewSet, basename='operator-get')
router.register(r'registrator', RegistratorViewSet, basename='registrator')

urlpatterns = [
    path('', include(router.urls)),
]