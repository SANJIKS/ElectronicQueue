import random
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Booking
from apps.qsystem.models import Queue

# Сериализатор для печати талона по предварительной записи
class RegisterCustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField()  # Поле для имени клиента
    last_name = serializers.CharField()  # Поле для фамилии клиента
    surname = serializers.CharField()  # Поле для отчества клиента
    pin = serializers.IntegerField()  # Поле для пин-кода клиента


#Сериализатор для модели Booking
class BookingSerializer(serializers.ModelSerializer):
    pin = serializers.IntegerField(read_only=True) # Поле для пин-кода бронирования (только для чтения)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user', 'branch', 'is_registered']


    def create(self, validated_data):
        pin = random.randint(100000, 999999)  # Генерация случайного пин-кода
        validated_data['pin'] = pin  # Установка сгенерированного пин-кода
        validated_data['user'] = self.context['request'].user  # Установка текущего пользователя

        return super().create(validated_data)
    

    def to_representation(self, instance):
        representation =  super().to_representation(instance)

        user_id = representation['user']
        user = User.objects.get(id=user_id)
        username = user.username
        first_name = user.profile.first_name
        last_name = user.profile.last_name
        surname = user.profile.surname

        representation['user'] = username  # Замена идентификатора пользователя на его имя пользователя
        representation['first_name'] = first_name  # Добавление имени пользователя 
        representation['last_name'] = last_name  # Добавление фамилии пользователя 
        representation['surname'] = surname  # Добавление отчества пользователя 

        queue = Queue.objects.get(pk=representation['queue'])  # Получение объекта очереди

        representation['branch'] = queue.branch.name  # Добавление названия филиала 
        representation['service'] = queue.services.name  # Добавление названия услуги 

        return representation