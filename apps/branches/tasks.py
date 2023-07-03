from celery import shared_task



@shared_task
def check_func():
<<<<<<< HEAD
    from .models import Window
    Window.objects.all().update(number_of_transfers=0)
=======

>>>>>>> 10fe5557 (save)
