from rest_framework import serializers
from .models import Window, Branch, Region

#Сериализатор для модели Region
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


#Сериализатор для модели Branch
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

