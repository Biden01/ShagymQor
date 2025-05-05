from django.db import models
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название управления")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Управление"
        verbose_name_plural = "Управления"

class TelegramUser(models.Model):
    user_id = models.BigIntegerField(unique=True, verbose_name="ID пользователя")
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name="Имя пользователя")
    first_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Фамилия")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (@{self.username})"

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('overdue', 'Просрочено'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name="Управление")
    message = models.TextField(verbose_name="Текст обращения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата выполнения")
    response = models.TextField(blank=True, verbose_name="Ответ")

    def __str__(self):
        return f"Обращение #{self.id} от {self.user}"

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ['-created_at']

class ComplaintHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, verbose_name="Обращение")
    status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES, verbose_name="Статус")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name="Управление")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История обращения"
        verbose_name_plural = "История обращений"
        ordering = ['-created_at']

class Notification(models.Model):
    TYPE_CHOICES = [
        ('deadline', 'Срок выполнения'),
        ('status', 'Изменение статуса'),
        ('response', 'Получен ответ'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, verbose_name="Обращение")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Тип уведомления")
    message = models.TextField(verbose_name="Текст уведомления")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']

class DepartmentKPI(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Управление")
    period = models.DateField(verbose_name="Период")
    total_complaints = models.IntegerField(default=0, verbose_name="Всего обращений")
    completed_complaints = models.IntegerField(default=0, verbose_name="Выполнено обращений")
    overdue_complaints = models.IntegerField(default=0, verbose_name="Просрочено обращений")
    average_response_time = models.DurationField(null=True, blank=True, verbose_name="Среднее время ответа")
    average_completion_time = models.DurationField(null=True, blank=True, verbose_name="Среднее время выполнения")
    satisfaction_rate = models.FloatField(default=0, verbose_name="Удовлетворенность")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "KPI управления"
        verbose_name_plural = "KPI управлений"
        unique_together = ['department', 'period']

class AIAnalysis(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, verbose_name="Обращение")
    suggested_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name="Предложенное управление")
    confidence_score = models.FloatField(default=0, verbose_name="Уверенность")
    keywords = models.JSONField(default=list, verbose_name="Ключевые слова")
    analysis_result = models.JSONField(default=dict, verbose_name="Результат анализа")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Анализ ИИ"
        verbose_name_plural = "Анализы ИИ"

class Report(models.Model):
    TYPE_CHOICES = [
        ('daily', 'Ежедневный'),
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('quarterly', 'Квартальный'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Тип отчета")
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    content = models.JSONField(verbose_name="Содержание отчета")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        ordering = ['-period_end']

class EmailNotification(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, verbose_name="Обращение")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=255, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Время отправки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email уведомление"
        verbose_name_plural = "Email уведомления"
        ordering = ['-created_at'] 