from django.contrib import admin
from .models import Branch, Ad, Board, Window, Region, Calendar, BaseCalendar, Floor, Cabinet

admin.site.register([Branch, Ad, Board, Window, Region, Calendar, BaseCalendar, Floor, Cabinet])
