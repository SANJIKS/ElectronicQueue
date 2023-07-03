from django.db import models
# from location_field.models.plain import PlainLocationField
from django.contrib.auth import get_user_model

User = get_user_model()

#Модель Области
class Region(models.Model):
    name = models.CharField(max_length=50) # Название области

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'


#Модель Филиала
class Branch(models.Model):
    name = models.CharField(max_length=200) #поле для хранения названия филиала
    phone = models.CharField(max_length=20)  # Поле для хранения телефона филиала
    admin = models.ForeignKey(User, related_name='branches', null=True, blank=True, on_delete=models.CASCADE)
    schedule_start = models.TimeField(default="9:00") # Начало рабочего дня
    schedule_end = models.TimeField(default="20:00") # Конец рабочего дня
    # location = PlainLocationField(based_fields=['city'], zoom=7) # Поле локации
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='branches', null=True, blank=True) # Поле для хранения области
    city = models.CharField(max_length=100, null=True, blank=True) # Город
    street = models.CharField(max_length=100, null=True, blank=True) # Улица


    def __str__(self):
        return f"Филиал {self.name}"
    
    class Meta:
        verbose_name = 'Филиал' 
        verbose_name_plural = 'Филиалы' 


#Модель Терминала
class Terminal(models.Model):
    number = models.PositiveSmallIntegerField()  # Поле для хранения номера терминала
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='terminals')  # Внешний ключ для связи с моделью филиала

    def __str__(self):
        return f"Терминал {self.number}"
    
    class Meta:
        verbose_name = 'Терминал' 
        verbose_name_plural = 'Терминалы'


#Модель Окна
class Window(models.Model):
    number = models.PositiveSmallIntegerField()  # Номер окна
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='windows')  # Филиал, к которому принадлежит окно
    operator = models.OneToOneField(User, on_delete=models.CASCADE)  # Оператор, назначенный на окно
    number_of_transfers = models.PositiveSmallIntegerField(default=0)  # Количество переводов на другое окно
    max_transfers = models.PositiveSmallIntegerField(default=5)  # Максимальное количество переводов
    is_online = models.BooleanField(default=False)  # Флаг, указывающий, на месте ли сотрудник
    schedule_start = models.IntegerField(default=9)  # Начало рабочего дня окна (часы)
    schedule_end = models.IntegerField(default=18)  # Конец рабочего дня окна (часы)
    is_busy = models.BooleanField(default=False)  # Флаг, указывающий, обслуживает ли оператор клиента

    def __str__(self):
        return f'Окно №{self.number} - {self.branch.name} - {self.operator.username}'
    
    class Meta:
        verbose_name = 'Окно'
        verbose_name_plural = "Окна"


class Calendar(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    holiday = models.CharField(max_length=100)
    date = models.DateField()