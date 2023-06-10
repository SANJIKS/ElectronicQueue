from django.db import models
from django.contrib.auth import get_user_model
from slugify import slugify

User = get_user_model()

class Queue(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Очередь'
        verbose_name_plural = 'Очереди'

class Customer(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='articles')
    ticket_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_served = models.BooleanField(default=False)
    served_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Customer {self.name} - Queue: {self.queue}"
    
    class Meta:
        verbose_name = 'Талон'
        verbose_name_plural = 'Талоны'
        ordering = ['ticket_number']