from rest_framework import serializers
from django.db.models import Max
from .models import Queue, Customer

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'  


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('user', 'ticket_number', 'is_served', 'served_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def create(self, validated_data):
        # Получаем максимальное значение ticket_number из базы данных
        max_ticket_number = Customer.objects.aggregate(Max('ticket_number'))['ticket_number__max']
        
        # Если в базе данных уже есть записи с ticket_number, увеличиваем значение на 1
        if max_ticket_number is not None:
            validated_data['ticket_number'] = max_ticket_number + 1
        else:
            # Если база данных пустая, задаем ticket_number равным 1
            validated_data['ticket_number'] = 1
        
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


    

    