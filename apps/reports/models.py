from django.db import models
from django.contrib.auth.models import User

from apps.qsystem.models import Customer

class OperatorDailyReport(models.Model):
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    date = models.DateField()
    total_served = models.PositiveIntegerField(default=0)
    average_time = models.PositiveIntegerField(default=0)
    max_time = models.PositiveIntegerField(default=0)
    min_time = models.PositiveIntegerField(default=0)
    operator_first_name = models.CharField(max_length=100, blank=True)
    operator_last_name = models.CharField(max_length=100, blank=True)
    operator_surname = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Operator Report'
        verbose_name_plural = 'Operator Reports'

    def __str__(self):
        return f'Report for {self.operator.username} - {self.date}'


class OperatorAction(models.Model):
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    created_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=150)


class CustomerAction(models.Model):
    Customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='actions')
    created_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=150)


