from django.urls import path, include
from rest_framework import routers
from .views import download_file, OperatorReportPDFView, OperatorWeekReportPDFView, OperatorServedReportExcelViewSet, OperatorCancelledReportExcelViewSet

router = routers.DefaultRouter()
router.register('operator-served/excel', OperatorServedReportExcelViewSet, basename='operator-served-excel')
router.register('operator-cancelled/excel', OperatorCancelledReportExcelViewSet, basename='operator-cancelled-excel')

urlpatterns = [
    path('', include(router.urls)),
    path('operator/<int:operator_id>/report/', OperatorReportPDFView.as_view(), name='operator_report_pdf'),
    path('operator/<int:operator_id>/week_report/', OperatorWeekReportPDFView.as_view(), name='operator_week_pdf'),
    path('report/', download_file),
]