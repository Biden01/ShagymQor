from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Complaint, Department
import re

@shared_task
def sync_instagram_complaints():
    """Задача для синхронизации жалоб из Instagram"""
    # TODO: Реализовать интеграцию с Instagram API
    pass

@shared_task
def notify_department_about_complaint(complaint_id):
    """Отправляет уведомление в управление о новой жалобе"""
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        if complaint.department and complaint.department.email:
            subject = f'Новая жалоба #{complaint.id}'
            message = f'''
            Поступила новая жалоба:
            
            ID: {complaint.id}
            От: {complaint.full_name or complaint.instagram_username or 'Аноним'}
            Содержание: {complaint.content}
            Срок исполнения: {complaint.deadline.strftime('%d.%m.%Y')}
            
            Для просмотра деталей перейдите по ссылке:
            http://shagymqor.kz/complaints/{complaint.id}/
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[complaint.department.email],
                fail_silently=False,
            )
            return True
    except Complaint.DoesNotExist:
        return False

@shared_task
def check_overdue_complaints():
    """Проверяет просроченные жалобы и обновляет их статус"""
    now = timezone.now()
    overdue_complaints = Complaint.objects.filter(
        status__in=['new', 'in_progress'],
        deadline__lt=now
    )
    
    for complaint in overdue_complaints:
        complaint.status = 'overdue'
        complaint.save()
        
        # Уведомляем управление о просрочке
        if complaint.department and complaint.department.email:
            subject = f'Жалоба #{complaint.id} просрочена'
            message = f'''
            Внимание! Жалоба #{complaint.id} просрочена.
            
            Срок исполнения: {complaint.deadline.strftime('%d.%m.%Y')}
            Статус изменен на: Просрочена
            
            Для просмотра деталей перейдите по ссылке:
            http://shagymqor.kz/complaints/{complaint.id}/
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[complaint.department.email],
                fail_silently=False,
            )
    
    return len(overdue_complaints)

@shared_task
def send_daily_report():
    """Отправляет ежедневный отчет о жалобах"""
    today = timezone.now().date()
    departments = Department.objects.all()
    
    for department in departments:
        if not department.email:
            continue
            
        # Статистика за день
        today_complaints = Complaint.objects.filter(
            department=department,
            created_at__date=today
        )
        new_count = today_complaints.filter(status='new').count()
        in_progress_count = today_complaints.filter(status='in_progress').count()
        completed_count = today_complaints.filter(status='completed').count()
        overdue_count = today_complaints.filter(status='overdue').count()
        
        subject = f'Ежедневный отчет по жалобам за {today.strftime("%d.%m.%Y")}'
        message = f'''
        Уважаемые сотрудники {department.name}!
        
        Статистика по жалобам за {today.strftime("%d.%m.%Y")}:
        
        Новых жалоб: {new_count}
        В обработке: {in_progress_count}
        Выполнено: {completed_count}
        Просрочено: {overdue_count}
        
        Общее количество: {today_complaints.count()}
        
        Для просмотра подробной информации перейдите в систему:
        http://shagymqor.kz/analytics/
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[department.email],
            fail_silently=False,
        )

@shared_task
def fetch_instagram_messages():
    """
    Задача для получения сообщений из Instagram
    и создания жалоб в системе
    """
    # Здесь будет реальная интеграция с Instagram Graph API
    # Для примера используем заглушку
    messages = get_instagram_messages()  # Предполагаемая функция
    
    for message in messages:
        # Проверяем, не существует ли уже жалоба с таким ID
        if not Complaint.objects.filter(instagram_id=message['id']).exists():
            # Определяем управление на основе ключевых слов
            department = assign_department(message['text'])
            
            # Создаем жалобу
            Complaint.objects.create(
                instagram_id=message['id'],
                instagram_username=message['username'],
                content=message['text'],
                department=department,
                deadline=timezone.now() + timezone.timedelta(days=7),  # Стандартный срок - 7 дней
            )

def assign_department(text):
    """
    Определяет управление на основе ключевых слов в тексте жалобы
    """
    keywords = {
        'транспорт|дорога|автобус|трамвай|троллейбус': 'transport',
        'благоустройство|парк|сквер|озеленение': 'landscaping',
        'жилье|квартира|дом|ремонт': 'housing',
        'образование|школа|детский сад': 'education',
        'здравоохранение|больница|поликлиника': 'healthcare',
    }
    
    for pattern, department_name in keywords.items():
        if re.search(pattern, text.lower()):
            try:
                return Department.objects.get(name__icontains=department_name)
            except Department.DoesNotExist:
                pass
    
    return None

@shared_task
def check_deadlines():
    """
    Проверяет сроки выполнения жалоб и отправляет уведомления
    """
    # Жалобы, срок которых истекает через 2 дня
    upcoming_deadlines = Complaint.objects.filter(
        status__in=['new', 'in_progress'],
        deadline__lte=timezone.now() + timezone.timedelta(days=2),
        deadline__gt=timezone.now()
    )
    
    for complaint in upcoming_deadlines:
        if complaint.department and complaint.department.email:
            send_mail(
                'Приближается срок выполнения жалобы',
                f'Жалоба #{complaint.id} должна быть выполнена до {complaint.deadline.strftime("%d.%m.%Y")}',
                settings.EMAIL_HOST_USER,
                [complaint.department.email],
                fail_silently=False,
            ) 