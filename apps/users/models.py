from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from djoser.signals import user_activated
from django.db import models

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_operator = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username



@receiver(user_activated)
def activate_user_handler(sender, user, request, **kwargs):
    if user.email.endswith('@rsk.com'):
        profile, created = Profile.objects.get_or_create(user=user)
        profile.is_operator = True
        profile.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)