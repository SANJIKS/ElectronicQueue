from datetime import date, datetime

from celery import shared_task
from django.utils import timezone
from pytz import timezone as timez

from apps.qsystem.models import Customer, Queue

today = datetime.now().astimezone(timez('Asia/Bishkek'))

@shared_task
def cancel_ticket(customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        if customer.operator:
            return
        
        queue = customer.queue
        if customer.number_of_calls == queue.max_calls:
            current_position = customer.position
            customer.is_served = False
            customer.save()
            
            other_customers = Customer.objects.filter(queue=queue, created_at__date=today, position__gt=current_position).exclude(pk=customer_id)

            for other_customer in other_customers:
                if other_customer.position > current_position:
                    other_customer.position -= 1
                    other_customer.save()     
        else:    
            current_position = customer.position
            customer.position = queue.customers.count() 
            customer.save()

            other_customers = Customer.objects.filter(queue=queue, created_at__date=today, position__gt=current_position).exclude(pk=customer_id)
            
            for other_customer in other_customers:
                if other_customer.position > current_position:
                    other_customer.position -= 1
                    other_customer.save()

    except Customer.DoesNotExist:
        pass


@shared_task
def shift_positions(pk, queue, current_position):
    other_customers = Customer.objects.filter(queue=queue, created_at__date=today, position__gt=current_position).exclude(pk=pk)
    for other_customer in other_customers:
        if other_customer.position is not None and other_customer.position > current_position:
            other_customer.position -= 1
            other_customer.save()


@shared_task
def calculate_average_waiting_time(queue_id):
    queue = Queue.objects.get(pk=queue_id)

    today = date.today()

    served_customers = Customer.objects.filter(queue=queue, is_served=True, created_at__date=today)
    total_served_customers = served_customers.count()

    total_waiting_time = sum(
        (customer.served_at - customer.created_at).seconds // 60 for customer in served_customers
    )
    average_waiting_time = (
        total_waiting_time // total_served_customers if total_served_customers > 0 else 0
    )

    queue.average_waiting_time = average_waiting_time
    queue.save()