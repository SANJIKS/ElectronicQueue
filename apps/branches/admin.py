from django.contrib import admin
from .models import Branch, Terminal, Window, Region, Calendar

admin.site.register([Branch, Terminal, Window, Region, Calendar])
