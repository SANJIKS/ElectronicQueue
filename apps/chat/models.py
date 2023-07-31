from django.db import models
from django.contrib.auth import get_user_model

from apps.branches.models import Branch

User = get_user_model()

class PrivateChat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats2')

class PrivateMessage(models.Model):
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)