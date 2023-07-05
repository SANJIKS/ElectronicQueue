from django.contrib import admin
from .models import Queue, Customer, Waiting_List, Services

admin.site.register([Queue, Customer, Waiting_List, Services])
