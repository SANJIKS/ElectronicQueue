from django.contrib import admin
from .models import OperatorDailyReport, OperatorAction, CustomerAction

admin.site.register([OperatorDailyReport, OperatorAction, CustomerAction])