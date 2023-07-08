from rest_framework import serializers
from .models import OperatorReport

class OperatorReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorReport
        fields = '__all__'
        read_only_fields = ('id',)