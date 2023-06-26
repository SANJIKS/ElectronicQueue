from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from djoser.signals import user_activated, user_registered
from django.db import models

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(
        upload_to='users', null=True, blank=True, default='users/default.jpg')
    bio = models.TextField(max_length=500, blank=True)
    banned = models.BooleanField(default=False)

    CHOISES = [
        ('guest', 'Гость'),
        ('operator', 'Оператор'),
        ('admin', 'Admin')
    ]

    position = models.CharField(max_length=20, choices=CHOISES, default='guest')


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