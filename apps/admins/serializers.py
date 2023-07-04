from rest_framework import serializers

class ChangeMaxCalls(serializers.Serializer):
    number = serializers.IntegerField()

class ChangePrintTime(serializers.Serializer):
    start = serializers.TimeField()
    end = serializers.TimeField()

class ChangeWaitingTime(serializers.Serializer):
    time = serializers.IntegerField()


class ChangeMaxTransfers(serializers.Serializer):
    number = serializers.IntegerField()