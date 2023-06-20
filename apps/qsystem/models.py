from django.db import models
from django.contrib.auth import get_user_model
from apps.branches.models import Branch, Terminal
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

User = get_user_model()

class Queue(models.Model):
    name = models.CharField(max_length=100)  # Поле для хранения имени очереди
    window_number = models.PositiveSmallIntegerField()  # Поле для хранения номера окна
    average_waiting_time = models.PositiveIntegerField(default=0)  # Поле для хранения среднего времени ожидания
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)  # Внешний ключ для связи с моделью филиала
    operator = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True) # Внешний ключ для связи с пользователем(оператором)
    kpi = models.FloatField(default=0) # Поле для хранения KPI сотрудника

    def __str__(self):
        return self.name  
    
    class Meta:
        verbose_name = 'Очередь' 
        verbose_name_plural = 'Очереди' 

class Customer(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)  # Внешний ключ для связи с моделью очереди
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')  # Внешний ключ для связи с моделью пользователей
    ticket_number = models.CharField(max_length=10)  # Поле для хранения номера талона
    position = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Поле для хранения даты и времени создания
    is_served = models.BooleanField(default=None, null=True)  # Поле для хранения статуса обслуживания
    served_at = models.DateTimeField(null=True, blank=True)  # Поле для хранения даты и времени обслуживания
    # terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, blank=True, null=True)  # Внешний ключ для связи с моделью терминала

    def __str__(self):
        return f"Customer {self.user.username} - Queue: {self.queue} - {self.ticket_number}" 
    
    class Meta:
        verbose_name = 'Талон'  
        verbose_name_plural = 'Талоны'  
        ordering = ['-position']  # Сортировка объектов по номеру талона


