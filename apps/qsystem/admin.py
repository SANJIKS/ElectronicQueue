from django.contrib import admin
from .models import Queue, Customer

admin.site.register([Queue, Customer])
