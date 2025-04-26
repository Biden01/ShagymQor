from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Complaint, Department, ComplaintHistory
from .forms import ComplaintForm, ComplaintFilterForm, DepartmentForm

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
                models.Q(content__icontains=search) |
                models.Q(full_name__icontains=search) |
                models.Q(contact_info__icontains=search)
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
        processing_time=models.F('updated_at') - models.F('created_at')
    ).aggregate(
        avg_time=Avg('processing_time')
    )
    
    # Статистика по управлениям
    department_stats = Department.objects.annotate(
        total_complaints=Count('complaint'),
        completed_complaints=Count('complaint', filter=models.Q(complaint__status='completed')),
        overdue_complaints=Count('complaint', filter=models.Q(complaint__status='overdue')),
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
            return redirect('department_list')

    context = {
        'departments': departments,
        'form': form,
    }
    return render(request, 'department_list.html', context)

def sync_instagram_messages():
    """Функция для синхронизации сообщений из Instagram"""
    # Здесь будет реализована логика получения сообщений через Instagram Graph API
    # и создания соответствующих жалоб
    pass 