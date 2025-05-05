from django.contrib import admin
from .models import (
    Department, TelegramUser, Complaint, ComplaintHistory, 
    Notification, DepartmentKPI, AIAnalysis, Report, EmailNotification
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'created_at')
    search_fields = ('username', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department', 'status', 'priority', 'created_at', 'deadline')
    list_filter = ('status', 'priority', 'department')
    search_fields = ('message', 'user__username', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'status', 'department', 'created_at')
    list_filter = ('status', 'department')
    search_fields = ('comment', 'complaint__message')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'complaint', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('message', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(DepartmentKPI)
class DepartmentKPIAdmin(admin.ModelAdmin):
    list_display = ('department', 'period', 'total_complaints', 'completed_complaints', 
                   'overdue_complaints', 'satisfaction_rate')
    list_filter = ('period', 'department')
    search_fields = ('department__name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'suggested_department', 'confidence_score', 'created_at')
    list_filter = ('suggested_department',)
    search_fields = ('complaint__message', 'keywords')
    readonly_fields = ('created_at',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('type', 'period_start', 'period_end', 'created_at')
    list_filter = ('type', 'period_start', 'period_end')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'complaint', 'email', 'subject', 'sent_at', 'created_at')
    list_filter = ('sent_at',)
    search_fields = ('subject', 'message', 'email')
    readonly_fields = ('created_at', 'sent_at') 