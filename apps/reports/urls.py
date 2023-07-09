from django.urls import path, include
from rest_framework import routers
from .views import OperatorServedReportExcelViewSet, OperatorCancelledReportExcelViewSet, OperatorStatisticReportPDFViewSet, OperatorGraphicReportWordViewSet, CustomersServedExcelViewSet, CustomersCancelledExcelViewSet, BookingReportViewSet

router = routers.DefaultRouter()
router.register('operator-served/excel', OperatorServedReportExcelViewSet, basename='operator-served-excel')
router.register('operator-cancelled/excel', OperatorCancelledReportExcelViewSet, basename='operator-cancelled-excel')
router.register('operator-time/pdf', OperatorStatisticReportPDFViewSet, basename='operator-time-pdf')
router.register('operator-average/word', OperatorGraphicReportWordViewSet, basename='operator-average-word')
router.register('customers-served/excel', CustomersServedExcelViewSet, basename='customers-served-excel')
router.register('customers-cancelled/excel', CustomersCancelledExcelViewSet, basename='customers-cancelled-excel')
router.register('booking-count/word', BookingReportViewSet, basename='booking-word')

urlpatterns = [
    path('', include(router.urls)),

]