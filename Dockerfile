# Используйте базовый образ Python
FROM python:3.11

# Установите переменную окружения PYTHONUNBUFFERED на 1
ENV PYTHONUNBUFFERED=1

# Установите рабочую директорию внутри контейнера
WORKDIR /code

# Скопируйте файл requirements.txt в контейнер
COPY requirements.txt /code/

# Установите зависимости проекта
RUN pip install -r requirements.txt

# Установка GDAL
RUN apt-get update && apt-get install -y gdal-bin

# Скопируйте все содержимое проекта в контейнер
COPY . /code/

# Запустите команду для запуска проекта Django

CMD ["python", "manage.py", "migrate"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]