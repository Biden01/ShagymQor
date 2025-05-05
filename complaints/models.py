from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Department(models.Model):
    """Модель для управления"""
    name = models.CharField(max_length=200, verbose_name="Название управления")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Управление"
        verbose_name_plural = "Управления"
        ordering = ['name']

    def __str__(self):
        return self.name

class Complaint(models.Model):
    """Модель для обращений"""
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
        ('rejected', 'Отклонено'),
    ]

    title = models.CharField(max_length=200, verbose_name="Тема обращения")
    message = models.TextField(verbose_name="Текст обращения")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Управление")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class ComplaintStatus(models.Model):
    """Модель для истории статусов обращения"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "История статуса"
        verbose_name_plural = "История статусов"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.title} - {self.get_status_display()}"

class ComplaintFile(models.Model):
    """Модель для файлов, прикрепленных к обращению"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='complaints/%Y/%m/%d/', verbose_name="Файл")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Файл обращения"
        verbose_name_plural = "Файлы обращений"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Файл к обращению {self.complaint.title}" 