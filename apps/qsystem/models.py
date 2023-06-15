from django.db import models
from django.contrib.auth import get_user_model
from slugify import slugify

User = get_user_model()

class Queue(models.Model):
    name = models.CharField(max_length=100)  # Поле для хранения имени очереди
    window_number = models.PositiveSmallIntegerField()  # Поле для хранения номера окна
    average_waiting_time = models.PositiveIntegerField(default=0)  # Поле для хранения среднего времени ожидания

    def __str__(self):
        return self.name  
    
    class Meta:
        verbose_name = 'Очередь' 
        verbose_name_plural = 'Очереди' 

class Customer(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)  # Внешний ключ для связи с моделью очереди
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')  # Внешний ключ для связи с моделью пользователей
    ticket_number = models.PositiveIntegerField()  # Поле для хранения номера талона
    created_at = models.DateTimeField(auto_now_add=True)  # Поле для хранения даты и времени создания
    is_served = models.BooleanField(default=False)  # Поле для хранения статуса обслуживания
    served_at = models.DateTimeField(null=True, blank=True)  # Поле для хранения даты и времени обслуживания

    def __str__(self):
        return f"Customer {self.user.username} - Queue: {self.queue}" 
    
    class Meta:
        verbose_name = 'Талон'  
        verbose_name_plural = 'Талоны'  
        ordering = ['ticket_number']  # Сортировка объектов по номеру талона