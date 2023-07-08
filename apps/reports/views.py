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
from .models import OperatorDailyReport



import tempfile

class OperatorReportPDFView(APIView):
    def get(self, request, operator_id):
        operator = User.objects.get(pk=operator_id)
        today = datetime.date.today()
        report = OperatorDailyReport.objects.filter(operator=operator, date=today).latest('id')

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
        reports = OperatorDailyReport.objects.filter(operator=operator, date__range=(week_start, today))

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


from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pandas as pd
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status



class OperatorHourReportPDFView(APIView):
    def get_reports_by_hour(self, operator, date, hour):
        reports = OperatorDailyReport.objects.filter(operator=operator, date=date, hour=hour)
        return reports

    def get(self, request, operator_id, date, hour):
        operator = get_object_or_404(User, pk=operator_id)
        reports = self.get_reports_by_hour(operator, date, hour)

        if not reports:
            return Response({'error': 'No reports available for the specified date and hour.'}, status=status.HTTP_404_NOT_FOUND)

        # График и формирование отчета за выбранный час
        x = ['Max Time', 'Min Time', 'Average Time']
        width = 0.4

        max_time = reports.values_list('max_time', flat=True)
        min_time = reports.values_list('min_time', flat=True)
        average_time = reports.values_list('average_time', flat=True)

        hours = range(len(x))

        plt.figure(figsize=(8, 6))

        plt.bar(hours, max_time, width=width, align='center', label='Max Time')
        plt.bar([h + width for h in hours], min_time, width=width, align='center', label='Min Time')
        plt.bar([h + 2 * width for h in hours], average_time, width=width, align='center', label='Average Time')

        plt.xlabel('Hour')
        plt.ylabel('Time (seconds)')
        plt.title(f'Operator Hourly Time Report - {operator.username} - {date} - Hour {hour}')
        plt.xticks(hours, x)
        plt.legend()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=operator_hour_report_{operator.username}_{date}_hour{hour}.pdf'

        canvas = FigureCanvas(plt.gcf())
        canvas.print_pdf(response)

        return response
    

from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from apps.qsystem.models import Customer
from drf_yasg.utils import swagger_auto_schema
from .serializers import OperatorHourExcelServedReport
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from drf_yasg import openapi



class OperatorServedReportExcelViewSet(ViewSet):

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(manual_parameters=[
        # openapi.Parameter(
        #     name='operator_id',
        #     in_=openapi.IN_QUERY,
        #     type=openapi.TYPE_INTEGER,
        #     required=True,
        #     description='ID of the operator'
        # ),
        openapi.Parameter(
            name='date',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
            required=True,
            description='Date in the format "YYYY-MM-DD"'
        ),
        openapi.Parameter(
            name='start_hour',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=True,
            description='Start hour (0-23)'
        ),
        openapi.Parameter(
            name='end_hour',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=True,
            description='End hour (0-23)'
        )
    ])
    def get_hour_report(self, request, pk=None):

        operator_id = pk
        date = request.query_params.get('date')
        start_hour = request.query_params.get('start_hour')
        end_hour = request.query_params.get('end_hour')


        operator = get_object_or_404(User, pk=operator_id)
        customers = self.get_customers_by_hour(operator, date, start_hour, end_hour)

        # Создание и форматирование рабочей книги Excel
        wb = Workbook()
        ws = wb.active
        ws.title = 'Hourly Report'

        # Запись заголовков столбцов
        ws['A1'] = 'ID'
        ws['B1'] = 'Номер талона'
        ws['C1'] = 'Время обслуживания(с)'
        ws['D1'] = 'Начало обслуживания'
        ws['E1'] = 'Конец обслуживания'
        ws['F1'] = 'Время ожидания'
        ws['G1'] = 'Номер окна'
        ws['H1'] = 'Номер паспорта'
        ws['I1'] = 'Категория'
        ws['J1'] = 'Оператор'
        ws['K1'] = 'Дата'
        ws['L1'] = 'Филиал'

        # Запись данных отчета
        row = 2
        for customer in customers:
            print(customer.served_start)  # Отладочное сообщение
            print(customer.served_at)  # Отладочное сообщениеъ

            served_start = customer.served_start.replace(tzinfo=None)
            served_at = customer.served_at.replace(tzinfo=None)

            ws.cell(row=row, column=1, value=customer.id)
            ws.cell(row=row, column=2, value=customer.ticket_number)
            ws.cell(row=row, column=3, value=(served_at - served_start).total_seconds())
            ws.cell(row=row, column=4, value=served_start.strftime('%H:%M:%S'))  # Форматирование времени
            ws.cell(row=row, column=5, value=served_at.strftime('%H:%M:%S'))
            ws.cell(row=row, column=6, value=(customer.served_start - customer.created_at).total_seconds())
            ws.cell(row=row, column=7, value=customer.window.number)
            ws.cell(row=row, column=8, value=customer.pasport)
            ws.cell(row=row, column=9, value=customer.category)
            ws.cell(row=row, column=10, value=customer.operator.username)
            ws.cell(row=row, column=11, value=customer.created_at.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=12, value=customer.queue.branch.name)

            for column in range(1, 11):
                column_letter = get_column_letter(column)
                cell = ws[column_letter + str(row)]
                ws.column_dimensions[column_letter].width = max(ws.column_dimensions[column_letter].width, len(str(cell.value)))

            row += 1

        # Установка выравнивания ячеек
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(horizontal='center')

        # Сохранение книги Excel в байтовый поток
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Отправка файла Excel в качестве ответа
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=operator_hour_report_{operator.username}_{date}_{start_hour}-{end_hour}.xlsx'
        response.write(output.getvalue())

        return response
    

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            name='date',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
            required=True,
            description='Date in the format "YYYY-MM-DD"'
        )
    ])
    def get_day_report(self, request, pk=None):

        operator_id = pk
        date = request.query_params.get('date')


        operator = get_object_or_404(User, pk=operator_id)
        customers = self.get_customers_by_day(operator, date)

        # Создание и форматирование рабочей книги Excel
        wb = Workbook()
        ws = wb.active
        ws.title = 'Hourly Report'

        # Запись заголовков столбцов
        ws['A1'] = 'ID'
        ws['B1'] = 'Номер талона'
        ws['C1'] = 'Время обслуживания(с)'
        ws['D1'] = 'Начало обслуживания'
        ws['E1'] = 'Конец обслуживания'
        ws['F1'] = 'Время ожидания'
        ws['G1'] = 'Номер окна'
        ws['H1'] = 'Номер паспорта'
        ws['I1'] = 'Категория'
        ws['J1'] = 'Оператор'
        ws['K1'] = 'Дата'
        ws['L1'] = 'Филиал'

        # Запись данных отчета
        row = 2
        for customer in customers:
            print(customer.served_start)  # Отладочное сообщение
            print(customer.served_at)  # Отладочное сообщениеъ

            served_start = customer.served_start.replace(tzinfo=None)
            served_at = customer.served_at.replace(tzinfo=None)

            ws.cell(row=row, column=1, value=customer.id)
            ws.cell(row=row, column=2, value=customer.ticket_number)
            ws.cell(row=row, column=3, value=(served_at - served_start).total_seconds())
            ws.cell(row=row, column=4, value=served_start.strftime('%H:%M:%S'))  # Форматирование времени
            ws.cell(row=row, column=5, value=served_at.strftime('%H:%M:%S'))
            ws.cell(row=row, column=6, value=(customer.served_start - customer.created_at).total_seconds())
            ws.cell(row=row, column=7, value=customer.window.number)
            ws.cell(row=row, column=8, value=customer.pasport)
            ws.cell(row=row, column=9, value=customer.category)
            ws.cell(row=row, column=10, value=customer.operator.username)
            ws.cell(row=row, column=11, value=customer.created_at.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=12, value=customer.queue.branch.name)

            for column in range(1, 11):
                column_letter = get_column_letter(column)
                cell = ws[column_letter + str(row)]
                ws.column_dimensions[column_letter].width = max(ws.column_dimensions[column_letter].width, len(str(cell.value)))

            row += 1

        # Установка выравнивания ячеек
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(horizontal='center')

        # Сохранение книги Excel в байтовый поток
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Отправка файла Excel в качестве ответа
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=operator_day_report_{operator.username}_{date}.xlsx'
        response.write(output.getvalue())

        return response
    

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            name='start_date',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
            required=True,
            description='Date in the format "YYYY-MM-DD"'
        ),
        openapi.Parameter(
            name='end_date',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE,
            required=True,
            description='Date in the format "YYYY-MM-DD"'
        )
    ])
    def get_days_report(self, request, pk=None):

        operator_id = pk
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')


        operator = get_object_or_404(User, pk=operator_id)
        customers = self.get_customers_by_days(operator, start_date, end_date)

        # Создание и форматирование рабочей книги Excel
        wb = Workbook()
        ws = wb.active
        ws.title = 'Hourly Report'

        # Запись заголовков столбцов
        ws['A1'] = 'ID'
        ws['B1'] = 'Номер талона'
        ws['C1'] = 'Время обслуживания(с)'
        ws['D1'] = 'Начало обслуживания'
        ws['E1'] = 'Конец обслуживания'
        ws['F1'] = 'Время ожидания'
        ws['G1'] = 'Номер окна'
        ws['H1'] = 'Номер паспорта'
        ws['I1'] = 'Категория'
        ws['J1'] = 'Оператор'
        ws['K1'] = 'Дата'
        ws['L1'] = 'Филиал'

        # Запись данных отчета
        row = 2
        for customer in customers:
            print(customer.served_start)  # Отладочное сообщение
            print(customer.served_at)  # Отладочное сообщениеъ

            served_start = customer.served_start.replace(tzinfo=None)
            served_at = customer.served_at.replace(tzinfo=None)

            ws.cell(row=row, column=1, value=customer.id)
            ws.cell(row=row, column=2, value=customer.ticket_number)
            ws.cell(row=row, column=3, value=(served_at - served_start).total_seconds())
            ws.cell(row=row, column=4, value=served_start.strftime('%H:%M:%S'))  # Форматирование времени
            ws.cell(row=row, column=5, value=served_at.strftime('%H:%M:%S'))
            ws.cell(row=row, column=6, value=(customer.served_start - customer.created_at).total_seconds())
            ws.cell(row=row, column=7, value=customer.window.number)
            ws.cell(row=row, column=8, value=customer.pasport)
            ws.cell(row=row, column=9, value=customer.category)
            ws.cell(row=row, column=10, value=customer.operator.username)
            ws.cell(row=row, column=11, value=customer.created_at.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=12, value=customer.queue.branch.name)

            for column in range(1, 11):
                column_letter = get_column_letter(column)
                cell = ws[column_letter + str(row)]
                ws.column_dimensions[column_letter].width = max(ws.column_dimensions[column_letter].width, len(str(cell.value)))

            row += 1

        # Установка выравнивания ячеек
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(horizontal='center')

        # Сохранение книги Excel в байтовый поток
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Отправка файла Excel в качестве ответа
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=operator_day_report_{operator.username}_{start_date}_{end_date}.xlsx'
        response.write(output.getvalue())

        return response
    

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            name='year',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_INT64,
            required=True,
            description='Date in the format "YYYY"')
    ])
    def get_year_report(self, request, pk=None):

        operator_id = pk
        year = request.query_params.get('year')


        operator = get_object_or_404(User, pk=operator_id)
        customers = self.get_customers_by_year(operator, year)

        # Создание и форматирование рабочей книги Excel
        wb = Workbook()
        ws = wb.active
        ws.title = 'Hourly Report'

        # Запись заголовков столбцов
        ws['A1'] = 'ID'
        ws['B1'] = 'Номер талона'
        ws['C1'] = 'Время обслуживания(с)'
        ws['D1'] = 'Начало обслуживания'
        ws['E1'] = 'Конец обслуживания'
        ws['F1'] = 'Время ожидания'
        ws['G1'] = 'Номер окна'
        ws['H1'] = 'Номер паспорта'
        ws['I1'] = 'Категория'
        ws['J1'] = 'Оператор'
        ws['K1'] = 'Дата'
        ws['L1'] = 'Филиал'

        # Запись данных отчета
        row = 2
        for customer in customers:
            print(customer.served_start)  # Отладочное сообщение
            print(customer.served_at)  # Отладочное сообщениеъ

            served_start = customer.served_start.replace(tzinfo=None)
            served_at = customer.served_at.replace(tzinfo=None)

            ws.cell(row=row, column=1, value=customer.id)
            ws.cell(row=row, column=2, value=customer.ticket_number)
            ws.cell(row=row, column=3, value=(served_at - served_start).total_seconds())
            ws.cell(row=row, column=4, value=served_start.strftime('%H:%M:%S'))  # Форматирование времени
            ws.cell(row=row, column=5, value=served_at.strftime('%H:%M:%S'))
            ws.cell(row=row, column=6, value=(customer.served_start - customer.created_at).total_seconds())
            ws.cell(row=row, column=7, value=customer.window.number)
            ws.cell(row=row, column=8, value=customer.pasport)
            ws.cell(row=row, column=9, value=customer.category)
            ws.cell(row=row, column=10, value=customer.operator.username)
            ws.cell(row=row, column=11, value=customer.created_at.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=12, value=customer.queue.branch.name)

            for column in range(1, 11):
                column_letter = get_column_letter(column)
                cell = ws[column_letter + str(row)]
                ws.column_dimensions[column_letter].width = max(ws.column_dimensions[column_letter].width, len(str(cell.value)))

            row += 1

        # Установка выравнивания ячеек
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(horizontal='center')

        # Сохранение книги Excel в байтовый поток
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Отправка файла Excel в качестве ответа
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=operator_day_report_{operator.username}_{year}.xlsx'
        response.write(output.getvalue())

        return response


    def get_customers_by_hour(self, operator, date, start_hour, end_hour):
        customers = Customer.objects.filter(operator=operator, served_start__date=date, served_start__hour__range=(start_hour, end_hour), is_served=True)
        return customers
    
    def get_customers_by_days(self, operator, start_date, end_date):
        customers = Customer.objects.filter(operator=operator, created_at__date__range=(start_date, end_date), is_served=True)
        return customers

    def get_customers_by_day(self, operator, date):
        customers = Customer.objects.filter(operator=operator, created_at__date=date, is_served=True)
        return customers
    
    def get_customers_by_year(self, operator, year):
        customers = Customer.objects.filter(operator=operator, created_at__year=year, is_served=True)
        return customers