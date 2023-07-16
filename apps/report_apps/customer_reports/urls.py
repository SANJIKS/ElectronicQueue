from django.urls import path, include
from rest_framework import routers
from .views import CustomersServedExcelViewSet, CustomersCancelledExcelViewSet, BookingReportViewSet

router = routers.DefaultRouter()
router.register('customers/served_count/excel', CustomersServedExcelViewSet, basename='customers-served-excel')
router.register('customers/cancelled_count/excel', CustomersCancelledExcelViewSet, basename='customers-cancelled-excel')
router.register('bookings/count/word', BookingReportViewSet, basename='booking-word')

urlpatterns = [
    path('', include(router.urls)),

]