from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from bot.models import Complaint, Department, ComplaintHistory, TelegramUser

def home(request):
    # Общая статистика
    total_complaints = Complaint.objects.count()
    in_progress_count = Complaint.objects.filter(status='in_progress').count()
    completed_count = Complaint.objects.filter(status='completed').count()
    
    # Просроченные обращения (старше 3 дней)
    three_days_ago = timezone.now() - timedelta(days=3)
    overdue_count = Complaint.objects.filter(
        status='in_progress',
        created_at__lt=three_days_ago
    ).count()
    
    # Последние обращения
    recent_complaints = Complaint.objects.select_related('department', 'user').order_by('-created_at')[:5]
    
    # Статистика по управлениям
    departments = Department.objects.annotate(
        complaint_count=Count('complaint')
    ).order_by('-complaint_count')
    
    department_names = [dept.name for dept in departments]
    department_counts = [dept.complaint_count for dept in departments]
    
    context = {
        'total_complaints': total_complaints,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'recent_complaints': recent_complaints,
        'department_names': department_names,
        'department_counts': department_counts,
    }
    
    return render(request, 'home.html', context)

@login_required
def complaint_list(request):
    """Список всех обращений"""
    if request.user.is_staff:
        # Для администраторов показываем все обращения
        complaints = Complaint.objects.all().select_related('department', 'user')
    else:
        # Для обычных пользователей пока показываем все обращения
        # В будущем здесь можно добавить связь между Django User и TelegramUser
        complaints = Complaint.objects.all().select_related('department', 'user')
    
    # Добавляем пагинацию
    paginator = Paginator(complaints, 10)  # 10 обращений на страницу
    page = request.GET.get('page')
    complaints = paginator.get_page(page)
    
    return render(request, 'complaints/list.html', {'complaints': complaints})

@login_required
def create_complaint(request):
    """Создание нового обращения"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        department_id = request.POST.get('department')
        
        if not all([title, message, department_id]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('create_complaint')
        
        department = get_object_or_404(Department, id=department_id)
        complaint = Complaint.objects.create(
            title=title,
            message=message,
            user=request.user,
            department=department
        )
        
        # Создаем начальный статус
        ComplaintHistory.objects.create(
            complaint=complaint,
            status='new',
            department=department
        )
        
        # Обработка прикрепленных файлов
        files = request.FILES.getlist('files')
        for file in files:
            ComplaintFile.objects.create(
                complaint=complaint,
                file=file,
                uploaded_by=request.user
            )
        
        messages.success(request, 'Обращение успешно создано')
        return redirect('complaint_detail', complaint_id=complaint.id)
    
    departments = Department.objects.all()
    return render(request, 'complaints/create.html', {'departments': departments})

@login_required
def complaint_detail(request, complaint_id):
    """Детальная информация об обращении"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Проверяем доступ
    if not (request.user.id == complaint.user.user_id or request.user.is_staff):
        messages.error(request, 'У вас нет доступа к этому обращению')
        return redirect('complaint_list')
    
    if request.method == 'POST' and complaint.status == 'in_progress':
        comment = request.POST.get('comment')
        if comment:
            ComplaintHistory.objects.create(
                complaint=complaint,
                status=complaint.status,
                department=complaint.department,
                comment=comment
            )
            messages.success(request, 'Комментарий добавлен')
            return redirect('complaint_detail', complaint_id=complaint.id)
    
    return render(request, 'complaints/detail.html', {
        'complaint': complaint
    })

@login_required
def add_comment(request, complaint_id):
    """Добавление комментария к обращению"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if not (request.user.id == complaint.user.user_id or request.user.is_staff):
        messages.error(request, 'У вас нет доступа к этому обращению')
        return redirect('complaint_list')
    
    if request.method == 'POST':
        comment = request.POST.get('comment')
        if comment:
            ComplaintHistory.objects.create(
                complaint=complaint,
                status=complaint.status,
                department=complaint.department,
                comment=comment
            )
            messages.success(request, 'Комментарий добавлен')
        else:
            messages.error(request, 'Комментарий не может быть пустым')
    
    return redirect('complaint_detail', complaint_id=complaint.id) 