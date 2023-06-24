from django.db import models
# from location_field.models.plain import PlainLocationField
from django.contrib.auth import get_user_model

User = get_user_model()


class Region(models.Model):
    name = models.CharField(max_length=50) # Название области

    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=200) #поле для хранения названия филиала
    phone = models.CharField(max_length=20)  # Поле для хранения телефона филиала
    admin = models.ForeignKey(User, related_name='branches', null=True, blank=True, on_delete=models.CASCADE)
    schedule_start = models.IntegerField(default=9) # Начало рабочего дня
    schedule_end = models.IntegerField(default=20) # Конец рабочего дня
    # location = PlainLocationField(based_fields=['city'], zoom=7) # Поле локации
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='branches', null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True) # Город
    street = models.CharField(max_length=100, null=True, blank=True) # Улица


    def __str__(self):
        return f"Филиал {self.name}"
    
    class Meta:
        verbose_name = 'Филиал' 
        verbose_name_plural = 'Филиалы' 


class Terminal(models.Model):
    number = models.PositiveSmallIntegerField()  # Поле для хранения номера терминала
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='terminals')  # Внешний ключ для связи с моделью филиала

    def __str__(self):
        return f"Терминал {self.number}"
    
    class Meta:
        verbose_name = 'Терминал' 
        verbose_name_plural = 'Терминалы'


class Window(models.Model):
    number = models.PositiveSmallIntegerField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='windows')
    operator = models.OneToOneField(User, on_delete=models.CASCADE)
    number_of_transfers = models.PositiveSmallIntegerField(default=0)
    max_transfers = models.PositiveSmallIntegerField(default=5)
    is_online = models.BooleanField(default=False)
    schedule_start = models.IntegerField(default=9)
    schedule_end = models.IntegerField(default=18)

    def __str__(self):
        return f'Окно №{self.number} - {self.branch.name} - {self.operator.username}'