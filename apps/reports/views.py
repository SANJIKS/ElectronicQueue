from django.http import FileResponse
from rest_framework.decorators import api_view
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@api_view(['GET'])
def download_file(request):
    file_path = BASE_DIR / 'reports' / 'graph.pdf'

    file = open(file_path, 'rb')

    response = FileResponse(file)

    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    return response


import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework.views import APIView
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import OperatorReport



import tempfile

class OperatorReportPDFView(APIView):
    def get(self, request, operator_id):
        operator = User.objects.get(pk=operator_id)
        today = datetime.date.today()
        report = OperatorReport.objects.filter(operator=operator, date=today).latest('id')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=operator_report_{operator.username}.pdf'

        with tempfile.NamedTemporaryFile(suffix='.png') as temp_file:
            plt.figure(figsize=(8, 6))
            x = ['Total Served', 'Average Time', 'Max Time', 'Min Time']
            y = [report.total_served, report.average_time, report.max_time, report.min_time]
            plt.bar(x, y)
            plt.xlabel('Metrics')
            plt.ylabel('Values')
            plt.title(f'Operator Report - {report.operator.username} ({report.date})')
            plt.savefig(temp_file.name, format='png')
            plt.close()

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont('Helvetica', 12)

            p.drawString(100, 100, f'Operator: {report.operator.username}')
            p.drawString(100, 120, f'Date: {report.date}')

            p.drawImage(temp_file.name, 100, 150, width=400, height=300)

            p.showPage()
            p.save()

            pdf = buffer.getvalue()
            buffer.close()

        response.write(pdf)

        return response
    

import os
from PyPDF2 import PdfReader

class OperatorWeekReportPDFView(APIView):
    def get(self, request, operator_id):
        operator = User.objects.get(pk=operator_id)
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=6)
        reports = OperatorReport.objects.filter(operator=operator, date__range=(week_start, today))

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=operator_week_report_{operator.username}.pdf'

        with tempfile.NamedTemporaryFile(suffix='.png') as tmp_file1, \
             tempfile.NamedTemporaryFile(suffix='.png') as tmp_file2:

            plt.figure(figsize=(8, 6))
            x = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            width = 0.15

            total_served = [0] * 7
            max_time = [0] * 7
            min_time = [0] * 7
            average_time = [0] * 7

            for report in reports:
                day_of_week = report.date.weekday()
                total_served[day_of_week] = report.total_served
                max_time[day_of_week] = report.max_time
                min_time[day_of_week] = report.min_time
                average_time[day_of_week] = report.average_time

            days = range(len(x))

            plt.bar(days, max_time, width=width, align='center', label='Max Time')
            plt.bar([d + width for d in days], min_time, width=width, align='center', label='Min Time')
            plt.bar([d + 2 * width for d in days], average_time, width=width, align='center', label='Average Time')

            plt.xlabel('Days of the Week')
            plt.ylabel('Time (seconds)')
            plt.title(f'Operator Weekly Time Report - {operator.username}')
            plt.xticks(days, x)
            plt.legend()

            plt.savefig(tmp_file1.name, format='png')
            plt.close()

            plt.figure(figsize=(8, 6))

            plt.bar(days, total_served, width=width, align='center', label='Total Served')

            plt.xlabel('Days of the Week')
            plt.ylabel('Number of Servings')
            plt.title(f'Operator Weekly Service Report - {operator.username}')
            plt.xticks(days, x)
            plt.legend()

            plt.savefig(tmp_file2.name, format='png')
            plt.close()

            p = canvas.Canvas(response, pagesize=letter)
            p.setFont('Helvetica', 12)

            p.drawString(100, 100, f'Operator: {operator.username}')
            p.drawString(100, 120, f'Week Start: {week_start}')
            p.drawString(100, 140, f'Week End: {today}')

            p.drawImage(tmp_file1.name, 100, 200, width=400, height=300)

            p.showPage()

            p.drawImage(tmp_file2.name, 100, 200, width=400, height=300)

            p.showPage()
            p.save()

        return response