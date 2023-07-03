from rest_framework import serializers
from .models import BaseCalendar, Window, Branch, Region, Calendar

#Сериализатор для модели Region
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
        read_only_fields = ('id',)


#Сериализатор для модели Branch
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ('id',)


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        fields = '__all__'
        read_only_fields = ('id',)


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = '__all__'
        read_only_fields = ('id',)

class BaseCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCalendar
        fields = '__all__'
        read_only_fields = ('id',)