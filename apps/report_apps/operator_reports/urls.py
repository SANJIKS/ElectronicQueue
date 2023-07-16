from django.urls import path, include
from rest_framework import routers
from .views import OperatorServedReportExcelViewSet, OperatorCancelledReportExcelViewSet, OperatorStatisticReportPDFViewSet, OperatorGraphicReportWordViewSet

router = routers.DefaultRouter()
router.register('served_customers/excel', OperatorServedReportExcelViewSet, basename='operator-served-excel')
router.register('cancelled_customers/excel', OperatorCancelledReportExcelViewSet, basename='operator-cancelled-excel')
router.register('served_times/pdf', OperatorStatisticReportPDFViewSet, basename='operator-time-pdf')
router.register('average_served_times/word', OperatorGraphicReportWordViewSet, basename='operator-average-word')

urlpatterns = [
    path('operator/', include(router.urls)),
]