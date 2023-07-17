from django.db import models

from apps.qsystem.models import Customer

class CustomerAction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='actions')
    created_at = models.DateTimeField(auto_now_add=True)
    CHOICES = [
        ('created', 'Создан'),
        ('cancelled', 'Отменен'),
        ('served', 'Обслужен'),
        ('shifted', 'Перевен')
    ]
    action = models.CharField(max_length=150, choices=CHOICES)
    event = models.CharField(max_length=150)


