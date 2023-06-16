from django.db import models

class Branch(models.Model):
    number = models.PositiveSmallIntegerField()  # Поле для хранения номера филиала
    address = models.CharField(max_length=200)  # Поле для хранения адреса филиала
    phone = models.CharField(max_length=20)  # Поле для хранения телефона филиала

    def __str__(self):
        return f"Филиал {self.number}"
    
    class Meta:
        verbose_name = 'Филиал' 
        verbose_name_plural = 'Филиалы' 


class Terminal(models.Model):
    number = models.PositiveSmallIntegerField()  # Поле для хранения номера терминала
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)  # Внешний ключ для связи с моделью филиала

    def __str__(self):
        return f"Терминал {self.number}"
    
    class Meta:
        verbose_name = 'Терминал' 
        verbose_name_plural = 'Терминалы'
