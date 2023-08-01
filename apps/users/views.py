from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.qsystem.models import Customer
from apps.qsystem.serializers import CustomerSerializer
from apps.report_apps.operator_reports.models import OperatorAction

from .models import Profile
from .serializers import ProfileSerializer




class ProfileView(viewsets.ViewSet):

    @swagger_auto_schema(
        operation_summary="Получить профиль пользователя",
        operation_description="""
        Эндпоинт для получения профиля пользователя. Необходимо передать токен пользователя"""
    )
    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    

    @swagger_auto_schema(
        operation_summary="Обновить профиль пользователя",
        operation_description="""
        Эндпоинт для полного обновления пользователя. Необходимо передать токен пользователя и новые данные"""
    )
    def put(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


    @swagger_auto_schema(
        operation_summary="Обновить профиль пользователя(партийно)",
        operation_description="""
        Эндпоинт для партийного обновления пользователя. Необходимо передать токен пользователя и новые данные"""
    )
    def patch(self, request):
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    


    @swagger_auto_schema(
        operation_summary="История талонов пользователя",
        operation_description="""
        Эндпоинт для получения истории талонов пользователя, необходимо передать его ФИО"""
    )
    @action(detail=False, methods=['get'])
    def user_history(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        surname = request.data.get('surname')
        tickets = Customer.objects.filter(first_name=first_name, last_name=last_name, surname=surname)  

        serializer = CustomerSerializer(tickets, many=True)  
        return Response(serializer.data)



    @swagger_auto_schema(
        operation_summary="Получить профиль по id",
        operation_description="""
        Эндпоинт для получения профиля пользователя по id профиля, необходимо передать id"""
    )
    @action(detail=True, methods=['get'])
    def get_retrieve(self, request, pk=None):
        profile = Profile.objects.get(pk=pk)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    

class OperatorProfileViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary='Протокол: "Оператор вошел в систему',
        operation_description="""
        Эндпоинт для создания протокола о входе в систему, необходимо кидать запрос от лица оператора"""
    )
    @action(detail=False, methods=['post'])
    def come_in_system(self, request):
        operator = self.request.user
        OperatorAction.objects.create(operator=operator, action='come', event='Оператор вошел в систему')
        return Response({'message': 'Протокол создан'}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_summary='Протокол: "Оператор вышел из системы',
        operation_description="""
        Эндпоинт для создания протокола о выходе из системы, необходимо кидать запрос от лица оператора"""
    )
    @action(detail=False, methods=['post'])
    def out_of_system(self, request):
        operator = self.request.user
        OperatorAction.objects.create(operator=operator, action='out', event='Оператор вышел из системы')
        return Response({'message': 'Протокол создан'}, status=status.HTTP_200_OK)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        operation_summary='Авторизация',
        operation_description='Эндпоинт для получения access и refresh токена'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_summary='JWT Refresh',
        operation_description='This endpoint is used for refreshing JWT token'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        operation_summary='JWT Verify',
        operation_description='This endpoint is used for verifying JWT token'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    

class CustomUserViewSet(DjoserViewSet):
    @swagger_auto_schema(operation_summary='Получить всех пользователей', operation_description="""Эндпоинт для получения всех""")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Мой аккаунт', operation_description="This endpoints is used for edit user's account")
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Регистрация пользователей', operation_description='This endpoint is used for creating a new user')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Получение пользователя по id', operation_description='This endpoint is used for retrieve get a user')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Обновить пользователя', operation_description='This endpoint is used for updating user details')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Обновить пользователя партийно', operation_description='This endpoint is used for partial updating user details')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Удалить пользователя', operation_description='This endpoint is used for deleting a user')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Активировать аккаунт', operation_description='This endpoint is used for activating a user')
    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        return super().activation(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary='Resend Activation', operation_description='This endpoint is used for resending activation to a user')
    @action(["post"], detail=False)
    def resend_activation(self, request, *args, **kwargs):
        return super().resend_activation(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Сменить пароль', operation_description='This endpoint is used for setting user password')
    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        return super().set_password(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Восстановить пароль', operation_description='This endpoint is used for resetting user password')
    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        return super().reset_password(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Восстановить пароль (Confirm)', operation_description='This endpoint is used for confirming password reset')
    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        return super().reset_password_confirm(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Сменить username', operation_description='This endpoint is used for setting username')
    @action(["post"], detail=False, url_path=f"set_{User.USERNAME_FIELD}")
    def set_username(self, request, *args, **kwargs):
        return super().set_username(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Восстановить username', operation_description='This endpoint is used for resetting username')
    @action(["post"], detail=False, url_path=f"reset_{User.USERNAME_FIELD}")
    def reset_username(self, request, *args, **kwargs):
        return super().reset_username(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary='Восстановить username (Confirm)', operation_description='This endpoint is used for confirming username reset')
    @action(["post"], detail=False, url_path=f"reset_{User.USERNAME_FIELD}_confirm")
    def reset_username_confirm(self, request, *args, **kwargs):
        return super().reset_username_confirm(request, *args, **kwargs)
