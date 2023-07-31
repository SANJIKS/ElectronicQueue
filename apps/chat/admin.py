from django.contrib import admin
from .models import PrivateChat, PrivateMessage, ChatGroup, Message

admin.site.register([PrivateMessage, PrivateChat, ChatGroup, Message])