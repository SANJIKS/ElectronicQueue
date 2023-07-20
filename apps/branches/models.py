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


class Board(models.Model):
    number = models.IntegerField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='boards')
    text_size = models.CharField(max_length=100)
    text = models.TextField()
    сoursive = models.BooleanField(default=False)
    italic = models.BooleanField(default=False)
    bold = models.BooleanField(default=False)
    speed = models.IntegerField(default=2)

class Ad(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='ads')
    content_type = models.CharField(max_length=10, choices=[('photo', 'Photo'), ('video', 'Video')])
    content = models.FileField(upload_to='ad_contents/')


class Floor(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    number = models.IntegerField()

class Cabinet(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    number = models.IntegerField()


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
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, null=True, blank=True)
    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'Окно №{self.number} - {self.branch.name} - {self.operator.username}'
    
    class Meta:
        verbose_name = 'Окно'
        verbose_name_plural = "Окна"


class Calendar(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    holiday = models.CharField(max_length=100)
    date = models.DateField()


class BaseCalendar(models.Model):
    holiday = models.CharField(max_length=100)
    date = models.DateField()

