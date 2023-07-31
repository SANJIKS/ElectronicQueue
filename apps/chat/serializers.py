from rest_framework import serializers
from .models import ChatGroup, Message, PrivateChat, PrivateMessage

class ChatGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGroup
        fields = ['id', 'branch', 'members']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'chat_group', 'sender', 'content', 'timestamp']
        read_only_fields = ('id', 'chat_group', 'sender', 'timestamp')

class PrivateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChat
        fields = ['id', 'user1', 'user2']

class PrivateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateMessage
        fields = ['id', 'private_chat', 'sender', 'content', 'timestamp']
        read_only_fields = ('id', 'private_chat', 'chat_group', 'sender', 'timestamp')