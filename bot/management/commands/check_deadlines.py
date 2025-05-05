from django.core.management.base import BaseCommand
from django.utils import timezone
from bot.services import NotificationService

class Command(BaseCommand):
    help = 'Проверяет сроки выполнения обращений и отправляет уведомления'

    def handle(self, *args, **options):
        notification_service = NotificationService()
        notification_service.check_deadlines()
        
        self.stdout.write(
            self.style.SUCCESS('Проверка сроков выполнена')
        ) 