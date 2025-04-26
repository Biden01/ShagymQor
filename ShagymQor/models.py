from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Department(models.Model):
    """Модель управления/отдела"""
    name = models.CharField(max_length=200, verbose_name=_('Название управления'))
    email = models.EmailField(verbose_name=_('Email ответственного'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))

    class Meta:
        verbose_name = _('Управление')
        verbose_name_plural = _('Управления')
        ordering = ['name']

    def __str__(self):
        return self.name

class Complaint(models.Model):
    """Модель жалобы"""
    STATUS_CHOICES = (
        ('new', _('Новая')),
        ('in_progress', _('В процессе')),
        ('completed', _('Выполнена')),
        ('overdue', _('Просрочена')),
    )

    # Основная информация
    full_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('ФИО гражданина'))
    contact_info = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('Контактные данные'))
    content = models.TextField(verbose_name=_('Содержание жалобы'))
    
    # Служебная информация
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name=_('Ответственное управление'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_('Статус'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата поступления'))
    deadline = models.DateTimeField(verbose_name=_('Срок исполнения'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата последнего изменения'))
    
    # Instagram данные
    instagram_id = models.CharField(max_length=100, unique=True, verbose_name=_('ID сообщения в Instagram'))
    instagram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Instagram пользователь'))
    
    # Метаданные
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name=_('Назначенный сотрудник'))
    priority = models.IntegerField(default=0, verbose_name=_('Приоритет'))
    tags = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Теги'))

    class Meta:
        verbose_name = _('Жалоба')
        verbose_name_plural = _('Жалобы')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['department']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Жалоба #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    def save(self, *args, **kwargs):
        """Переопределяем метод save для автоматической проверки просрочки"""
        if self.status != 'completed' and self.deadline < timezone.now():
            self.status = 'overdue'
        super().save(*args, **kwargs)

class ComplaintHistory(models.Model):
    """Модель для отслеживания истории изменений жалобы"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    field = models.CharField(max_length=50)
    old_value = models.CharField(max_length=500, null=True)
    new_value = models.CharField(max_length=500, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('История изменений')
        verbose_name_plural = _('История изменений')
        ordering = ['-changed_at']

    def __str__(self):
        return f"Изменение {self.field} в жалобе #{self.complaint.id}" 