import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShagymQor.settings')

# Создание экземпляра приложения Celery
app = Celery('ShagymQor')

# Загружаем настройки из файла settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически загружаем задачи из всех приложений
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    'check-complaint-deadlines': {
        'task': 'bot.tasks.check_complaint_deadlines',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 