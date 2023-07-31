from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.serializers import ProfileSerializer

User = get_user_model()

from apps.branches.models import Window
from apps.qsystem.models import Customer

class ShiftWindow(serializers.Serializer):
    window = serializers.CharField()


class GetServedCustomers(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class GetCustomersHistory(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    surname = serializers.CharField()


class GetByProps(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    surname = serializers.CharField()
    phone = serializers.CharField()
    pasport = serializers.CharField()
    

class ChangeNotes(serializers.Serializer):
    notes = serializers.CharField()


class GetWindowsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        fields = '__all__'
    
    def get_queues(self, instance):
        queues = instance.queues.all()
        return [queue for queue in queues]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        operator = User.objects.get(pk=representation['operator'])
        
        queues = self.get_queues(operator)
        representation['queues'] = [queue.name for queue in queues]


        #Нужно будет добавить проверку на сегодняшний день, и при создании date=today
        customers_count = Customer.objects.filter(queue__in=queues, is_served__isnull=True).count()
        representation['customers'] = customers_count        
        
        representation['operator'] = f"{operator.profile.first_name} {operator.profile.last_name}"
        return representation
    

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer() # Assuming the related name is 'profile'

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile', ) 