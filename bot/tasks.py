from django.utils import timezone
from datetime import timedelta
from .services import KPICalculator, NotificationService
from .models import Department, Report
from celery import shared_task
from bot.models import Complaint, ComplaintHistory
import logging

logger = logging.getLogger(__name__)

def generate_daily_report():
    """Генерирует ежедневный отчет"""
    now = timezone.now()
    period_start = now - timedelta(days=1)
    
    # Генерируем KPI для каждого управления
    calculator = KPICalculator()
    for department in Department.objects.all():
        calculator.calculate_department_kpi(department, period_start, now)
    
    # Создаем общий отчет
    Report.objects.create(
        type='daily',
        period_start=period_start.date(),
        period_end=now.date(),
        content={
            'generated_at': now.isoformat(),
            'period': {
                'start': period_start.isoformat(),
                'end': now.isoformat()
            }
        }
    )

@shared_task
def check_complaint_deadlines():
    """
    Проверяет сроки обращений и обновляет их статусы
    """
    try:
        # Получаем все активные обращения
        active_complaints = Complaint.objects.filter(
            status__in=['new', 'in_progress']
        )
        
        now = timezone.now()
        
        for complaint in active_complaints:
            # Проверяем сроки в зависимости от типа обращения
            if complaint.status == 'new':
                # Новые обращения должны быть рассмотрены в течение 5 дней
                if now - complaint.created_at > timedelta(days=5):
                    complaint.status = 'overdue'
                    complaint.save()
                    
                    # Создаем запись в истории
                    ComplaintHistory.objects.create(
                        complaint=complaint,
                        status='overdue',
                        department=complaint.department,
                        comment='Превышен срок рассмотрения обращения'
                    )
                    
                    logger.info(f"Обращение #{complaint.id} помечено как просроченное")
            
            elif complaint.status == 'in_progress':
                # Обращения в работе должны быть завершены в течение 15 дней
                if now - complaint.created_at > timedelta(days=15):
                    complaint.status = 'overdue'
                    complaint.save()
                    
                    # Создаем запись в истории
                    ComplaintHistory.objects.create(
                        complaint=complaint,
                        status='overdue',
                        department=complaint.department,
                        comment='Превышен срок выполнения обращения'
                    )
                    
                    logger.info(f"Обращение #{complaint.id} помечено как просроченное")
        
        logger.info("Проверка сроков обращений завершена успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке сроков обращений: {str(e)}")
        raise

def generate_weekly_report():
    """Генерирует еженедельный отчет"""
    now = timezone.now()
    period_start = now - timedelta(days=7)
    
    Report.objects.create(
        type='weekly',
        period_start=period_start.date(),
        period_end=now.date(),
        content={
            'generated_at': now.isoformat(),
            'period': {
                'start': period_start.isoformat(),
                'end': now.isoformat()
            }
        }
    )

def generate_monthly_report():
    """Генерирует ежемесячный отчет"""
    now = timezone.now()
    period_start = now - timedelta(days=30)
    
    Report.objects.create(
        type='monthly',
        period_start=period_start.date(),
        period_end=now.date(),
        content={
            'generated_at': now.isoformat(),
            'period': {
                'start': period_start.isoformat(),
                'end': now.isoformat()
            }
        }
    )

def generate_quarterly_report():
    """Генерирует квартальный отчет"""
    now = timezone.now()
    period_start = now - timedelta(days=90)
    
    Report.objects.create(
        type='quarterly',
        period_start=period_start.date(),
        period_end=now.date(),
        content={
            'generated_at': now.isoformat(),
            'period': {
                'start': period_start.isoformat(),
                'end': now.isoformat()
            }
        }
    ) 