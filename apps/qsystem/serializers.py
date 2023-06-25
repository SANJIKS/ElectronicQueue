from datetime import datetime, timedelta
from pytz import timezone

from rest_framework import serializers
from django.db import models
from django.db.models import Max
from django.contrib.auth import get_user_model

from .models import Queue, Customer, Waiting_List


User = get_user_model()

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue  
        fields = '__all__'  
        read_only_fields = ('average_waiting_time',)  


class WaitingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waiting_List
        fields = '__all__'


class GetQueueCustomersSerializer(serializers.ModelSerializer):
    in_queue_time = serializers.SerializerMethodField()

    def get_in_queue_time(self, instance):
        created_at = instance.created_at
        current_time = datetime.now(timezone('Asia/Bishkek')).astimezone(timezone('Asia/Bishkek'))

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at).astimezone(timezone('Asia/Bishkek'))

        time_diff = current_time - created_at

        total_minutes = int(time_diff.total_seconds() // 60)
        return total_minutes
    
    class Meta:
        model = Customer
        fields = ('id', 'ticket_number', 'queue',  'category', 'in_queue_time')

    def to_representation(self, instance):
        representation =  super().to_representation(instance)
        representation['queue'] = instance.queue.name
        return representation
    

class CustomerListSerializer(serializers.ListSerializer):
    def get_in_queue_time(self, instance):
        created_at = instance.created_at
        current_time = datetime.now(timezone('Asia/Bishkek')).astimezone(timezone('Asia/Bishkek'))

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at).astimezone(timezone('Asia/Bishkek'))

        time_diff = current_time - created_at

        total_minutes = int(time_diff.total_seconds() // 60)
        return total_minutes
    

    def to_representation(self, data):
        iterable = data.all() if isinstance(data, models.Manager) else data
        return [{
            'id': item.pk,
            'ticket_number': item.ticket_number,
            'queue': item.queue.name,
            'waiting_time': self.get_in_queue_time(item),
            'category': item.category,
            'position': item.position
        } for item in iterable]

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer  
        fields = '__all__'  
        read_only_fields = ('user','time', 'ticket_number', 'is_served', 'served_at', 'position', 'served_start', 'number_of_calls', 'notes', 'operator', 'window', 'old_operator',)
        list_serializer_class = CustomerListSerializer

    def to_representation(self, instance):
        queue = instance.queue
        representation = super().to_representation(instance)
        created_at = representation['created_at']
        current_time = datetime.now(timezone('Asia/Bishkek')).astimezone(timezone('Asia/Bishkek'))

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at).astimezone(timezone('Asia/Bishkek'))

        time_diff = current_time - created_at

        total_minutes = int(time_diff.total_seconds() // 60)

        representation['minutes_in_queue'] = total_minutes
        representation['queue'] = queue.name

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
        try:
            representation['branch'] = instance.window.branch.name
        except:
            representation['branch'] = None
        return representation
    
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
        
        print(f"{queue.symbol}{max_ticket_number:02d}")
        return f"{queue.symbol}{max_ticket_number:02d}"



    

    