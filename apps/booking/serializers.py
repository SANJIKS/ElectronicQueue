import random
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Booking
from apps.qsystem.models import Queue

class RegisterCustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    surname = serializers.CharField()
    pin = serializers.IntegerField()

class BookingSerializer(serializers.ModelSerializer):
    pin = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user', 'branch', 'is_registered']

    def create(self, validated_data):
        pin = random.randint(100000, 999999)
        validated_data['pin'] = pin
        validated_data['user'] = self.context['request'].user

        return super().create(validated_data)
    
    def to_representation(self, instance):
        representation =  super().to_representation(instance)

        user_id = representation['user']
        user = User.objects.get(id=user_id)
        username = user.username
        first_name = user.profile.first_name
        last_name = user.profile.last_name
        surname = user.profile.surname

        representation['user'] = username
        representation['first_name'] = first_name
        representation['last_name'] = last_name
        representation['surname'] = surname

        queue = Queue.objects.get(pk=representation['queue'])

        representation['branch'] = queue.branch.name
        representation['service'] = queue.services.name
        return representation