from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from apps.branches.models import Branch
from apps.qsystem.models import Queue

class Booking(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='bookings')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='bookings')
    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pin = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
