from django.contrib import admin
from .models import Branch, Terminal, Window

admin.site.register([Branch, Terminal, Window])
