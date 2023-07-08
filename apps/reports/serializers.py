from rest_framework import serializers
from .models import OperatorDailyReport

class OperatorReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorDailyReport
        fields = '__all__'
        read_only_fields = ('id',)


class OperatorHourExcelServedReport(serializers.Serializer):
    start_hour = serializers.TimeField()
    end_hour = serializers.TimeField()
    date = serializers.DateField()