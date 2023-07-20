from rest_framework import serializers

from .models import (BaseCalendar, Branch, Cabinet, Calendar, Floor, Region,
                     Window, Board, Ad)


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

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ('id',)

class CabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = '__all__'
        read_only_fields = ('id',)



class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = '__all__'

class BoardSerializer(serializers.ModelSerializer):
    ads = AdSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = '__all__'