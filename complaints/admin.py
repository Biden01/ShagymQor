from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Department, Complaint, ComplaintHistory

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at', 'updated_at')
    search_fields = ('name', 'email')
    ordering = ('name',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'department', 'status', 'created_at', 'deadline')
    list_filter = ('status', 'department', 'created_at')
    search_fields = ('full_name', 'content', 'instagram_username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('full_name', 'contact_info', 'content')
        }),
        (_('Служебная информация'), {
            'fields': ('department', 'status', 'deadline', 'assigned_to', 'priority')
        }),
        (_('Instagram данные'), {
            'fields': ('instagram_id', 'instagram_username')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'tags')
        }),
    )

@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'changed_by', 'field', 'changed_at')
    list_filter = ('changed_at', 'changed_by')
    search_fields = ('complaint__id', 'field')
    ordering = ('-changed_at',)
    readonly_fields = ('complaint', 'changed_by', 'field', 'old_value', 'new_value', 'changed_at')
