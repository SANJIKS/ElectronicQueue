from django.contrib import admin
from .models import PrivateChat, PrivateMessage

admin.site.register([PrivateMessage, PrivateChat])