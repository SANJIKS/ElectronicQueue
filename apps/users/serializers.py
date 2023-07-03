from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Profile
from apps.branches.models import Window
from apps.qsystem.models import Customer

class GetByProps(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    surname = serializers.CharField()
    phone = serializers.CharField()
    pasport = serializers.CharField()
    

class ChangeNotes(serializers.Serializer):
    notes = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

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
        print(queues)
        representation['queues'] = [queue.name for queue in queues]

        today = timezone.localdate()

        #Нужно будет добавить проверку на сегодняшний день, и при создании date=today
        customers_count = Customer.objects.filter(queue__in=queues, is_served__isnull=True).count()
        representation['customers'] = customers_count        
        
        representation['operator'] = f"{operator.profile.first_name} {operator.profile.last_name}"
        return representation