from rest_framework import serializers
from django.db.models import Max
from .models import Queue, Customer

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'
        read_only_fields = ('average_waiting_time',)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('user', 'ticket_number', 'is_served', 'served_at',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def create(self, validated_data):
        max_ticket_number = Customer.objects.aggregate(Max('ticket_number'))['ticket_number__max']
        
        if max_ticket_number is not None:
            validated_data['ticket_number'] = max_ticket_number + 1
        else:
            validated_data['ticket_number'] = 1
        
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


    

    