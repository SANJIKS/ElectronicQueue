from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from djoser.signals import user_activated, user_registered
from django.db import models

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Пользователь
    first_name = models.CharField(max_length=100, null=True, blank=True) # Имя
    last_name = models.CharField(max_length=100, null=True, blank=True) # Фамилия
    surname = models.CharField(max_length=100, null=True, blank=True) # Отчество
    phone = models.CharField(max_length=50, null=True, blank=True) # Номер телефона
    birth_date = models.DateField(null=True, blank=True) # Дата рождения
    avatar = models.ImageField(
        upload_to='users', null=True, blank=True, default='users/default.jpg') # Изображение профиля
    bio = models.TextField(max_length=500, blank=True) # Доп. Инфо
    banned = models.BooleanField(default=False) # Флаг, указывающий, заблокирован ли пользователь

    CHOISES = [
        ('guest', 'Гость'),
        ('operator', 'Оператор'),
        ('admin', 'Admin')
    ]

    position = models.CharField(max_length=20, choices=CHOISES, default='guest') # Должность


    def __str__(self):
        return self.user.username



@receiver(user_activated)
def activate_user_handler(sender, user, request, **kwargs):
    if user.email.endswith('@rsk.com'):
        profile, created = Profile.objects.get_or_create(user=user)
        profile.position = 'operator'
        profile.save()

@receiver(user_registered)
def activate_user_auto(sender, user, request, **kwargs):
    user.is_active = True
    user.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)