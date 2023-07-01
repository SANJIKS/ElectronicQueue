from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from apps.branches.models import Branch
from apps.qsystem.models import Queue

class Booking(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='bookings') # Очередь(Услуга)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    pasport = models.CharField(max_length=40, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    time = models.TimeField(null=True, blank=True) # Время бронирования
    date = models.DateField(null=True, blank=True) # Дата бронирования
    created_at = models.DateTimeField(auto_now_add=True) # Дата и время создания бронирования
    pin = models.IntegerField() # Пин-код бронирования
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True) # Пользователь
    is_registered = models.BooleanField(default=False) # Флаг, указывающий, распечатан ли талон

    def __str__(self):
        return f"{self.queue} - {self.user}"
    
    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
