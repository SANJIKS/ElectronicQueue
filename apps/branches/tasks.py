from celery import shared_task
from datetime import date

from .models import Window
from apps.qsystem.models import Customer

today = date.today()

@shared_task
def refresh():
    Window.objects.all().update(number_of_transfers=0)
    Customer.objects.filter(is_served=None, created_at__date=today).update(is_served=False)
