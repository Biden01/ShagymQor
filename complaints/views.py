from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Complaint, Department, ComplaintHistory, MediaFile
from .forms import ComplaintForm, ComplaintFilterForm, DepartmentForm, UserRegistrationForm, MediaFileForm
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import login

@login_required
def complaint_list(request):
    """Список жалоб с фильтрацией"""
    form = ComplaintFilterForm(request.GET)
    complaints = Complaint.objects.all()

    if form.is_valid():
        if form.cleaned_data['department']:
            complaints = complaints.filter(department=form.cleaned_data['department'])
        if form.cleaned_data['status']:
            complaints = complaints.filter(status=form.cleaned_data['status'])
        if form.cleaned_data['date_from']:
            complaints = complaints.filter(created_at__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            complaints = complaints.filter(created_at__date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data['search']:
            search = form.cleaned_data['search']
            complaints = complaints.filter(
                Q(content__icontains=search) |
                Q(full_name__icontains=search) |
                Q(contact_info__icontains=search)
            )

    context = {
        'complaints': complaints,
        'form': form,
    }
    return render(request, 'complaint_list.html', context)

@login_required
def complaint_detail(request, pk):
    """Детальная информация о жалобе"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            # Сохраняем историю изменений
            for field in form.changed_data:
                old_value = getattr(complaint, field)
                new_value = form.cleaned_data[field]
                ComplaintHistory.objects.create(
                    complaint=complaint,
                    changed_by=request.user,
                    field=field,
                    old_value=str(old_value),
                    new_value=str(new_value)
                )
            
            form.save()
            messages.success(request, _('Изменения сохранены'))
            return redirect('complaint_detail', pk=pk)
    else:
        form = ComplaintForm(instance=complaint)

    context = {
        'complaint': complaint,
        'form': form,
        'history': complaint.history.all()[:10],
    }
    return render(request, 'complaint_detail.html', context)

@login_required
def analytics(request):
    """Страница аналитики"""
    # Статистика по статусам
    status_stats = Complaint.objects.values('status').annotate(count=Count('id'))
    
    # Среднее время обработки
    avg_processing_time = Complaint.objects.filter(
        status='completed'
    ).annotate(
        processing_time=F('updated_at') - F('created_at')
    ).aggregate(
        avg_time=Avg('processing_time')
    )
    
    # Преобразуем среднее время в дни и часы
    if avg_processing_time['avg_time']:
        total_seconds = avg_processing_time['avg_time'].total_seconds()
        avg_processing_time['days'] = int(total_seconds // 86400)  # 86400 секунд в дне
        avg_processing_time['hours'] = int((total_seconds % 86400) // 3600)  # 3600 секунд в часе
    else:
        avg_processing_time['days'] = 0
        avg_processing_time['hours'] = 0
    
    # Статистика по управлениям
    department_stats = Department.objects.annotate(
        total_complaints=Count('complaint'),
        completed_complaints=Count('complaint', filter=Q(complaint__status='completed')),
        overdue_complaints=Count('complaint', filter=Q(complaint__status='overdue')),
    )
    
    # Жалобы, требующие внимания
    urgent_complaints = Complaint.objects.filter(
        deadline__lte=timezone.now() + timedelta(days=2),
        status__in=['new', 'in_progress']
    ).order_by('deadline')

    context = {
        'status_stats': status_stats,
        'avg_processing_time': avg_processing_time['avg_time'],
        'department_stats': department_stats,
        'urgent_complaints': urgent_complaints,
    }
    return render(request, 'analytics.html', context)

@login_required
def department_list(request):
    """Список управлений"""
    departments = Department.objects.all()
    form = DepartmentForm()
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Управление добавлено'))
            return redirect('complaints:department_list')

    context = {
        'departments': departments,
        'form': form,
    }
    return render(request, 'department_list.html', context)

@login_required
def department_edit(request, pk):
    """Редактирование управления"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, _('Изменения сохранены'))
            return redirect('complaints:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
    }
    return render(request, 'department_edit.html', context)

@login_required
def department_delete(request, pk):
    """Удаление управления"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.delete()
        messages.success(request, _('Управление удалено'))
        return redirect('complaints:department_list')
    
    context = {
        'department': department,
    }
    return render(request, 'department_delete.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('complaints:complaint_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def create_complaint(request):
    if request.method == 'POST':
        complaint_form = ComplaintForm(request.POST)
        media_form = MediaFileForm(request.POST, request.FILES)
        
        if complaint_form.is_valid():
            complaint = complaint_form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            
            if media_form.is_valid():
                media_file = media_form.save(commit=False)
                media_file.complaint = complaint
                media_file.save()
            
            messages.success(request, _('Жалоба успешно создана'))
            return redirect('complaint_detail', pk=complaint.pk)
    else:
        complaint_form = ComplaintForm()
        media_form = MediaFileForm()
    
    return render(request, 'complaints/complaint_create.html', {
        'complaint_form': complaint_form,
        'media_form': media_form
    })
