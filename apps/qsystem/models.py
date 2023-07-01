from django.db import models
from django.contrib.auth import get_user_model
from apps.branches.models import Branch, Terminal
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from apps.branches.models import Window

User = get_user_model()

#Модель Категории Услуги
class Services(models.Model):
    CHOISES = [
        ('individuals', 'Физические лица'),
        ('legal entities', 'Юридические лица'),
        ('payment cards', 'Платежные карты')
    ]

    name = models.CharField(max_length=100, choices=CHOISES) # Название Категории


#Модель Очереди(Услуги)
class Queue(models.Model): 
    name = models.CharField(max_length=100)  # Поле для хранения имени очереди
    branch = models.ForeignKey(Branch, default=1, related_name='queues', on_delete=models.CASCADE) # Филиал
    description = models.CharField(max_length=200, blank=True, null=True) # Поле для хранения описания очереди
    documents = models.CharField(max_length=500, null=True, blank=True) # Документы
    optional_documents = models.CharField(max_length=500, null=True, blank=True) # Необязательные документы
    average_waiting_time = models.PositiveIntegerField(default=0)  # Поле для хранения среднего времени ожидания
    max_waiting_time = models.PositiveIntegerField(default=30) # Поле для хранения максимального времени ожидания
    operator = models.ManyToManyField(User, related_name='queues') # Связь с моделью пользователя (оператора)
    symbol = models.CharField(max_length=2, null=True, blank=True) # Символ очереди
    services = models.ForeignKey(Services, on_delete=models.CASCADE, related_name='queues', null=True, blank=True) # Тип услуги


    def __str__(self):
        return f'{self.name}-{self.branch.name}'  

    class Meta:
        verbose_name = 'Очередь' 
        verbose_name_plural = 'Очереди' 


#Модель Талона
class Customer(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='customers')  # Внешний ключ для связи с моделью очереди
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers_at_user')  # Внешний ключ для связи с моделью пользователей
    ticket_number = models.CharField(max_length=10)  # Поле для хранения номера талона
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    pasport = models.CharField(max_length=40, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True) # Поле для хранения позиции в очереди
    created_at = models.DateTimeField(auto_now_add=True)  # Поле для хранения даты и времени создания
    is_served = models.BooleanField(default=None, null=True)  # Поле для хранения статуса обслуживания
    served_start = models.DateTimeField(default=None, null=True, blank=True) # Поле для хранения начала времени обслуживания
    served_at = models.DateTimeField(null=True, blank=True)  # Поле для хранения даты и времени обслуживания
    operator = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='customers_at_operator') # Оператор обслуживший талон
    window = models.ForeignKey(Window, null=True, blank=True, on_delete=models.CASCADE, related_name='customers') # Номер окна
    old_operator = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='customers_at_old_operator') # Предыдущий оператор
    number_of_calls = models.PositiveSmallIntegerField(default=0) # Количество вызовов этого талона к оператору

    CATEGORY_CHOICES = [
        ('regular', 'Обычный'),
        ('booked', 'По записи'),
        ('pensioner', 'Пенсионер'),
        ('pregnant', 'Беременная'),
        ('veteran', 'Ветеран'),
        ('disabled person', 'С ограниченными возможностями')
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES) # Поле для хранения категории посетителя
    notes = models.CharField(max_length=200, null=True, blank=True) # Дополнительные сведения о талоне
    time = models.TimeField(null=True, blank=True) # Время предварительной записи

    def __str__(self):
        return f"Customer {self.first_name} {self.last_name} - Queue: {self.queue} - {self.ticket_number}" 
    
    class Meta:
        verbose_name = 'Талон'  
        verbose_name_plural = 'Талоны'  
        ordering = ['-created_at']  


#Модель Листа Ожидания
class Waiting_List(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE) # Связь с талоном
    created_at = models.DateTimeField(auto_now_add=True) # Дата создания

    def __str__(self):
        return self.customer.ticket_number
    
    class Meta:
        verbose_name = 'Лист ожидания'  
        verbose_name_plural = 'Лист ожидания'  



    
