import os
from celery import Celery

# Установите переменную окружения "DJANGO_SETTINGS_MODULE" на имя вашего файла настроек Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Загрузите конфигурацию из файла настроек Django.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживайте и регистрируйте задачи из файлов tasks.py в приложениях Django.
app.autodiscover_tasks()