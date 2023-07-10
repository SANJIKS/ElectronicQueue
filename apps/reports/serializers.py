from rest_framework import serializers
from apps.qsystem.models import Customer
from .models import OperatorDailyReport, OperatorAction, CustomerAction

class OperatorReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorDailyReport
        fields = '__all__'
        read_only_fields = ('id',)


class OperatorActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorAction
        fields = '__all__'
        read_only_fields = ('id',)



class CustomerActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAction
        fields = '__all__'
        read_only_fields = ('id',)