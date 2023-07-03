from celery import shared_task
from django.utils import timezone
from apps.qsystem.models import Customer


@shared_task
def cancel_ticket(customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        # Проверяем, что талон еще не обслуживается
        if customer.operator:
            return
        if (timezone.now() - customer.served_start).total_seconds() >= 120:
            customer.is_served = False
            customer.position = 0
            customer.save()
            queue = customer.queue
            other_customers = queue.customers.exclude(pk=customer.id)
            for other_customer in other_customers:
                if other_customer.position > customer.position:
                    other_customer.position -= 1
                    other_customer.save()
    except Customer.DoesNotExist:
        pass