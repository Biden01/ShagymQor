from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bot.models import Report, Complaint, Department
from bot.services import KPICalculator

class Command(BaseCommand):
    help = 'Генерирует отчеты по обращениям'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['daily', 'weekly', 'monthly', 'quarterly'],
            default='daily',
            help='Тип отчета'
        )

    def handle(self, *args, **options):
        report_type = options['type']
        now = timezone.now()
        
        # Определяем период отчета
        if report_type == 'daily':
            period_start = now - timedelta(days=1)
            period_end = now
        elif report_type == 'weekly':
            period_start = now - timedelta(days=7)
            period_end = now
        elif report_type == 'monthly':
            period_start = now - timedelta(days=30)
            period_end = now
        else:  # quarterly
            period_start = now - timedelta(days=90)
            period_end = now

        # Собираем статистику
        total_complaints = Complaint.objects.filter(
            created_at__range=(period_start, period_end)
        ).count()

        completed_complaints = Complaint.objects.filter(
            created_at__range=(period_start, period_end),
            status='completed'
        ).count()

        overdue_complaints = Complaint.objects.filter(
            created_at__range=(period_start, period_end),
            status='overdue'
        ).count()

        # Статистика по управлениям
        department_stats = {}
        for department in Department.objects.all():
            dept_complaints = Complaint.objects.filter(
                department=department,
                created_at__range=(period_start, period_end)
            )
            
            department_stats[department.name] = {
                'total': dept_complaints.count(),
                'completed': dept_complaints.filter(status='completed').count(),
                'overdue': dept_complaints.filter(status='overdue').count(),
                'in_progress': dept_complaints.filter(status='in_progress').count(),
            }

        # Создаем отчет
        report_content = {
            'period': {
                'start': period_start.isoformat(),
                'end': period_end.isoformat()
            },
            'total_complaints': total_complaints,
            'completed_complaints': completed_complaints,
            'overdue_complaints': overdue_complaints,
            'completion_rate': (completed_complaints / total_complaints * 100) if total_complaints > 0 else 0,
            'department_stats': department_stats
        }

        Report.objects.create(
            type=report_type,
            period_start=period_start.date(),
            period_end=period_end.date(),
            content=report_content
        )

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создан {report_type} отчет')
        ) 