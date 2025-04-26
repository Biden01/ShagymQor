from django.core.management.base import BaseCommand
from complaints.models import Department, Complaint
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Импорт тестовых данных в базу данных'

    def handle(self, *args, **options):
        # Создаем тестовые управления
        departments = [
            {'name': 'Управление транспорта', 'email': 'transport@example.com'},
            {'name': 'Управление благоустройства', 'email': 'landscaping@example.com'},
            {'name': 'Управление жилищно-коммунального хозяйства', 'email': 'housing@example.com'},
            {'name': 'Управление образования', 'email': 'education@example.com'},
            {'name': 'Управление здравоохранения', 'email': 'healthcare@example.com'},
        ]

        for dept_data in departments:
            Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'email': dept_data['email']}
            )

        # Создаем тестового пользователя
        User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Тестовый',
                'last_name': 'Пользователь',
                'is_staff': True
            }
        )

        # Создаем тестовые жалобы
        test_complaints = [
            {
                'content': 'На улице Ленина разбита дорога, нужен ремонт',
                'department': 'Управление транспорта',
                'status': 'new',
                'deadline': timezone.now() + timedelta(days=7)
            },
            {
                'content': 'В парке Горького сломаны скамейки',
                'department': 'Управление благоустройства',
                'status': 'in_progress',
                'deadline': timezone.now() + timedelta(days=3)
            },
            {
                'content': 'В школе №1 протекает крыша',
                'department': 'Управление образования',
                'status': 'completed',
                'deadline': timezone.now() - timedelta(days=1)
            },
            {
                'content': 'В поликлинике №2 нет лекарств',
                'department': 'Управление здравоохранения',
                'status': 'overdue',
                'deadline': timezone.now() - timedelta(days=5)
            }
        ]

        for complaint_data in test_complaints:
            department = Department.objects.get(name=complaint_data['department'])
            Complaint.objects.get_or_create(
                content=complaint_data['content'],
                defaults={
                    'department': department,
                    'status': complaint_data['status'],
                    'deadline': complaint_data['deadline'],
                    'instagram_id': f'test_{timezone.now().timestamp()}',
                    'instagram_username': 'test_user'
                }
            )

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно импортированы')) 