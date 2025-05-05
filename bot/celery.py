from celery import Celery
from celery.schedules import crontab

app = Celery('bot')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Регистрируем задачи
app.autodiscover_tasks(['bot.tasks'])

# Настройки периодических задач
app.conf.beat_schedule = {
    'generate-daily-report': {
        'task': 'bot.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
    'check-complaint-deadlines': {
        'task': 'bot.tasks.check_complaint_deadlines',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
    },
    'generate-weekly-report': {
        'task': 'bot.tasks.generate_weekly_report',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),  # Каждый понедельник
    },
    'generate-monthly-report': {
        'task': 'bot.tasks.generate_monthly_report',
        'schedule': crontab(hour=0, minute=0, day=1),  # Первое число каждого месяца
    },
    'generate-quarterly-report': {
        'task': 'bot.tasks.generate_quarterly_report',
        'schedule': crontab(hour=0, minute=0, day=1, month='*/3'),  # Первое число каждого квартала
    }
} 