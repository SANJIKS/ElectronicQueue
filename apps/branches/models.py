from django.db import models
from location_field.models.plain import PlainLocationField

class Branch(models.Model):
    name = models.CharField(max_length=200) #поле для хранения названия филиала
    address = models.CharField(max_length=200)  # Поле для хранения адреса филиала
    phone = models.CharField(max_length=20)  # Поле для хранения телефона филиала
    location = PlainLocationField(based_fields=['city'], zoom=7)

    def __str__(self):
        return f"Филиал {self.name}"
    
    class Meta:
        verbose_name = 'Филиал' 
        verbose_name_plural = 'Филиалы' 


class Terminal(models.Model):
    number = models.PositiveSmallIntegerField()  # Поле для хранения номера терминала
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)  # Внешний ключ для связи с моделью филиала

    def __str__(self):
        return f"Терминал {self.number}"
    
    class Meta:
        verbose_name = 'Терминал' 
        verbose_name_plural = 'Терминалы'
