from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Queue, Customer
from .serializers import QueueSerializer, CustomerSerializer

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer

    def get_permissions(self):
        # Проверяем права доступа только для создания очереди
        if self.action == 'create' and not self.request.user.is_superuser:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # Создаем очередь с помощью сериализатора
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_permissions(self):
        # Проверяем права доступа только для создания пользователя в очереди
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     # Получаем переданный queue_id из сериализатора
    #     queue_id = serializer.validated_data.get('queue_id')
        
    #     # Проверяем, существует ли очередь с указанным queue_id
    #     if not Queue.objects.filter(id=queue_id).exists():
    #         return Response({"error": "Такой очереди не существует."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Вычисляем ticket_number для нового пользователя
    #     ticket_number = Customer.objects.filter(queue_id=queue_id).count() + 1

    #     if not request.user.is_authenticated:
    #         return Response({"error": "Вы должны быть зарегистрированы."}, status=status.HTTP_401_UNAUTHORIZED)

    #     # Создаем нового пользователя в очереди
    #     customer = Customer.objects.create(queue_id=queue_id, ticket_number=ticket_number)
    #     serializer = self.serializer_class(customer)
    #     return Response(serializer.data)

    # def update(self, request, *args, **kwargs):
    #     # Обновляем статус обслуживания пользователя
    #     instance = self.get_object()
    #     instance.is_served = True
    #     instance.served_at = datetime.now()
    #     instance.save()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)
