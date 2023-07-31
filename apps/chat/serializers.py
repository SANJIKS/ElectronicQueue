from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PrivateChat, PrivateMessage

User = get_user_model()

class PrivateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChat
        fields = ['id', 'user1', 'user2']

class PrivateMessageSerializer(serializers.ModelSerializer):
    private_chat_id = serializers.PrimaryKeyRelatedField(source='private_chat', queryset=PrivateChat.objects.all())
    sender = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = PrivateMessage
        fields = ['id', 'content', 'timestamp', 'private_chat_id', 'sender']

    def create(self, validated_data):
        private_message = PrivateMessage.objects.create(**validated_data)
        return private_message