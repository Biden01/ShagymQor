from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Complaint
from .tasks import notify_department_about_complaint

@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    """Обработчик сигнала сохранения жалобы"""
    if created:
        # Отправляем уведомление в управление о новой жалобе
        notify_department_about_complaint.delay(instance.id) 