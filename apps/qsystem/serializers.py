import re
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
        read_only_fields = ('user', 'ticket_number', 'is_served', 'served_at', 'position',) 

    def create(self, validated_data):
        queue = validated_data['queue']
        ticket_number = self.get_ticket_number(queue)

        validated_data['ticket_number'] = ticket_number
        validated_data['user'] = self.context['request'].user

        position = Customer.objects.filter(queue=queue).aggregate(Max('position'))
        last_position = position.get('position__max')

        if last_position is not None:
            validated_data['position'] = last_position + 1
        else:
            validated_data['position'] = 1

        
        return super().create(validated_data)  # Создать объект с использованием базового метода create()
    
    def get_ticket_number(self, queue):
        if queue is None:
            return ""

        max_ticket_number = Customer.objects.filter(queue=queue).aggregate(Max('ticket_number'))
        last_ticket_number = max_ticket_number.get('ticket_number__max')

        if last_ticket_number is not None:
            max_ticket_number = int(last_ticket_number[2:]) + 1
        else:
            max_ticket_number = 1
        
        print(f"{queue.name.upper()[0]}{queue.window_number}{max_ticket_number:02d}")
        return f"{queue.name.upper()[0]}{queue.window_number}{max_ticket_number:02d}"



    

    