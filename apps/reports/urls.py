from django.urls import path, include
from .views import download_file, OperatorReportPDFView, OperatorWeekReportPDFView

urlpatterns = [
    path('operator/<int:operator_id>/report/', OperatorReportPDFView.as_view(), name='operator_report_pdf'),
    path('operator/<int:operator_id>/week_report/', OperatorWeekReportPDFView.as_view(), name='operator_week_pdf'),
    path('report/', download_file),
]