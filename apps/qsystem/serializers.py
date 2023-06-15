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
        max_ticket_number = Customer.objects.aggregate(Max('ticket_number'))['ticket_number__max']  # Максимальный номер талона
        
        if max_ticket_number is not None:
            validated_data['ticket_number'] = max_ticket_number + 1  # Увеличить номер талона на 1, если есть предыдущие талоны
        else:
            validated_data['ticket_number'] = 1  # Установить номер талона 1, если нет предыдущих талонов
        
        validated_data['user'] = self.context['request'].user  # Задать пользователя из контекста запроса в validated_data
        return super().create(validated_data)  # Создать объект с использованием базового метода create()



    

    