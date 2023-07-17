import datetime
from django.contrib.auth.models import User
from .models import OperatorDailyReport
from apps.qsystem.models import Customer
from celery import shared_task

@shared_task
def generate_operator_report():
    today = datetime.date.today()
    operators = User.objects.filter(queues__isnull=False)
    
    for operator in operators:
        total_served = 0
        total_time = 0
        max_time = 0
        min_time = float('inf')

        # Получаем все талоны, обслуженные оператором сегодня
        served_customers = Customer.objects.filter(
            operator=operator,
            served_at__date=today,
            is_served=True
        )

        for customer in served_customers:
            served_time = (customer.served_at - customer.served_start).total_seconds()

            # Увеличиваем счетчики
            total_served += 1
            total_time += served_time
            max_time = max(max_time, served_time)
            min_time = min(min_time, served_time)

        # Получаем ФИО оператора
        operator_first_name = operator.profile.first_name if operator.profile and operator.profile.first_name else 'Оператор'
        operator_last_name = operator.profile.last_name if operator.profile and operator.profile.last_name else 'Операторов'
        operator_surname = operator.profile.surname if operator.profile and operator.profile.surname else 'Операторович'

        # Обработка деления на ноль
        average_time = total_time // total_served if total_served > 0 else 0

        if min_time == float('inf'):
            min_time = 0

        # Создаем отчет оператора
        OperatorDailyReport.objects.create(
            operator=operator,
            date=today,
            total_served=total_served,
            average_time=average_time,
            max_time=max_time,
            min_time=min_time,
            operator_first_name=operator_first_name,
            operator_last_name=operator_last_name,
            operator_surname=operator_surname
        )