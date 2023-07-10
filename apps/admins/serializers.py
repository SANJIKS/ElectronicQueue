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


class GetOnlineWindows(serializers.Serializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    surname = serializers.SerializerMethodField()
    profile_pk = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    window_number = serializers.SerializerMethodField()
    window_pk = serializers.SerializerMethodField()

    def get_first_name(self, instance):
        return instance.profile.first_name

    def get_last_name(self, instance):
        return instance.profile.last_name

    def get_surname(self, instance):
        return instance.profile.surname

    def get_profile_pk(self, instance):
        return instance.profile.pk

    def get_position(self, instance):
        return instance.profile.position

    def get_window_number(self, instance):
        return instance.window.number

    def get_window_pk(self, instance):
        return instance.window.pk

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation
    
