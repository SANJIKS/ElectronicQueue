from rest_framework import serializers
from apps.qsystem.models import Customer
from .models import CustomerAction

class CustomerActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAction
        fields = '__all__'
        read_only_fields = ('id',)