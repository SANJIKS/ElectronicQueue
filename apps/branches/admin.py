from django.contrib import admin
from .models import Branch, Terminal

admin.site.register([Branch, Terminal])
