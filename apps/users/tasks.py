from datetime import datetime
from pytz import timezone as timez

from celery import shared_task
from django.utils import timezone
from apps.qsystem.models import Customer


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
            
            today = datetime.now().astimezone(timez('Asia/Bishkek'))
            other_customers = Customer.objects.filter(queue=queue, created_at__date=today, position__gt=current_position).exclude(pk=customer_id)

            for other_customer in other_customers:
                if other_customer.position > current_position:
                    other_customer.position -= 1
                    other_customer.save()     
        else:    
            current_position = customer.position
            customer.position = queue.customers.count() + 1
            customer.save()

            today = datetime.now().astimezone(timez('Asia/Bishkek'))
            other_customers = Customer.objects.filter(queue=queue, created_at__date=today, position__gt=current_position).exclude(pk=customer_id)
            
            for other_customer in other_customers:
                if other_customer.position > current_position:
                    other_customer.position -= 1
                    other_customer.save()

    except Customer.DoesNotExist:
        pass

