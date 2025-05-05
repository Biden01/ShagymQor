from django.utils import timezone
from datetime import timedelta
from .models import Complaint, Department, AIAnalysis, DepartmentKPI, Notification, EmailNotification
from django.db import models
from asgiref.sync import sync_to_async

class ComplaintAnalyzer:
    def __init__(self):
        # Словарь ключевых слов для каждого управления
        self.department_keywords = {
            '🚗 Транспорт и дороги': [
                'дорога', 'транспорт', 'автобус', 'трамвай', 'метро', 'парковка', 'светофор',
                'пробка', 'асфальт', 'яма', 'тротуар', 'пешеход', 'переход', 'остановка',
                'такси', 'маршрут', 'разметка', 'знак', 'регулировщик'
            ],
            '🏗 Строительство': [
                'строительство', 'ремонт', 'здание', 'дом', 'стройка', 'подъезд', 'крыша',
                'фундамент', 'стена', 'окно', 'дверь', 'лифт', 'лестница', 'фасад',
                'балкон', 'подвал', 'чердак', 'забор', 'ограждение'
            ],
            '🌳 Экология': [
                'экология', 'мусор', 'отходы', 'воздух', 'вода', 'почва', 'зелень',
                'дерево', 'куст', 'цветок', 'газон', 'парк', 'сквер', 'озеро',
                'река', 'загрязнение', 'выброс', 'дым', 'шум'
            ],
            '🔧 ЖКХ': [
                'жкх', 'вода', 'отопление', 'электричество', 'канализация', 'газ',
                'квартира', 'дом', 'подъезд', 'лифт', 'мусор', 'уборка', 'ремонт',
                'управляющая компания', 'тариф', 'счет', 'оплата', 'квартплата'
            ],
            '📚 Образование': [
                'школа', 'детский сад', 'образование', 'учитель', 'ученик', 'класс',
                'урок', 'учебник', 'директор', 'завуч', 'столовая', 'спортзал',
                'библиотека', 'кружок', 'секция', 'олимпиада', 'экзамен'
            ],
            '🏥 Здравоохранение': [
                'больница', 'поликлиника', 'врач', 'медицина', 'здоровье', 'лечение',
                'аптека', 'прививка', 'анализ', 'диагноз', 'терапевт', 'педиатр',
                'стоматолог', 'скорая', 'рецепт', 'медикамент', 'процедура'
            ],
            '👥 Социальная защита': [
                'соцзащита', 'пенсия', 'пособие', 'льгота', 'инвалид', 'пенсионер',
                'малоимущий', 'многодетный', 'сирота', 'беженец', 'бесплатно',
                'компенсация', 'выплата', 'поддержка', 'помощь', 'защита'
            ]
        }

    def analyze_text(self, text: str) -> dict:
        """
        Анализирует текст обращения и определяет релевантное управление
        """
        text = text.lower()
        scores = {}
        
        # Подсчет совпадений ключевых слов
        for dept, keywords in self.department_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[dept] = score
        
        if not scores:
            return {
                'department': '📋 Другое',
                'confidence': 0.0,
                'keywords': []
            }
        
        # Определяем управление с наибольшим количеством совпадений
        max_score = max(scores.values())
        total_score = sum(scores.values())
        best_dept = max(scores.items(), key=lambda x: x[1])[0]
        
        # Находим использованные ключевые слова
        used_keywords = [
            keyword for keyword in self.department_keywords[best_dept]
            if keyword in text
        ]
        
        return {
            'department': best_dept,
            'confidence': max_score / total_score if total_score > 0 else 0.0,
            'keywords': used_keywords
        }

    @sync_to_async
    def save_analysis(self, complaint_id: int, analysis_result: dict) -> None:
        """
        Сохраняет результат анализа в базу данных
        """
        from .models import Complaint, Department, AIAnalysis
        
        complaint = Complaint.objects.get(id=complaint_id)
        department, _ = Department.objects.get_or_create(
            name=analysis_result['department'],
            defaults={'description': f'Управление {analysis_result["department"]}'}
        )
        
        AIAnalysis.objects.create(
            complaint=complaint,
            suggested_department=department,
            confidence_score=analysis_result['confidence'],
            keywords=analysis_result['keywords'],
            analysis_result=analysis_result
        )

class KPICalculator:
    def calculate_department_kpi(self, department: Department, period_start: timezone.datetime, 
                               period_end: timezone.datetime) -> DepartmentKPI:
        """Рассчитывает KPI для управления за указанный период"""
        complaints = Complaint.objects.filter(
            department=department,
            created_at__range=(period_start, period_end)
        )

        total = complaints.count()
        completed = complaints.filter(status='completed').count()
        overdue = complaints.filter(status='overdue').count()

        # Расчет среднего времени ответа
        response_times = []
        for complaint in complaints:
            if complaint.response:
                response_time = complaint.updated_at - complaint.created_at
                response_times.append(response_time)

        avg_response_time = sum(response_times, timedelta()) / len(response_times) if response_times else None

        # Расчет среднего времени выполнения
        completion_times = []
        for complaint in complaints.filter(status='completed'):
            if complaint.completed_at:
                completion_time = complaint.completed_at - complaint.created_at
                completion_times.append(completion_time)

        avg_completion_time = sum(completion_times, timedelta()) / len(completion_times) if completion_times else None

        # Расчет удовлетворенности (можно расширить на основе отзывов)
        satisfaction_rate = (completed / total * 100) if total > 0 else 0

        kpi = DepartmentKPI.objects.create(
            department=department,
            period=period_end.date(),
            total_complaints=total,
            completed_complaints=completed,
            overdue_complaints=overdue,
            average_response_time=avg_response_time,
            average_completion_time=avg_completion_time,
            satisfaction_rate=satisfaction_rate
        )

        return kpi

class NotificationService:
    @sync_to_async
    def send_notification(self, complaint: Complaint, notification_type: str, message: str):
        """Отправляет уведомление пользователю"""
        notification = Notification.objects.create(
            user=complaint.user,
            complaint=complaint,
            type=notification_type,
            message=message
        )
        return notification

    def send_email_notification(self, complaint: Complaint, email: str, subject: str, message: str):
        """Отправляет email-уведомление"""
        email_notification = EmailNotification.objects.create(
            user=complaint.user,
            complaint=complaint,
            email=email,
            subject=subject,
            message=message
        )
        # Здесь должна быть логика отправки email
        return email_notification

    def check_deadlines(self):
        """Проверяет сроки выполнения обращений и отправляет уведомления"""
        now = timezone.now()
        upcoming_deadlines = Complaint.objects.filter(
            status__in=['new', 'in_progress'],
            deadline__isnull=False,
            deadline__gt=now,
            deadline__lte=now + timedelta(days=1)
        )

        for complaint in upcoming_deadlines:
            self.send_notification(
                complaint,
                'deadline',
                f'Напоминание: срок выполнения обращения #{complaint.id} истекает через 24 часа'
            )

class DeadlineTracker:
    def __init__(self):
        self.priority_deadlines = {
            'low': timedelta(days=15),
            'medium': timedelta(days=10),
            'high': timedelta(days=5)
        }

    @sync_to_async
    def check_deadlines(self) -> None:
        """
        Проверяет сроки выполнения обращений и отправляет уведомления
        """
        from .models import Complaint, Notification, DepartmentKPI
        from django.utils import timezone
        
        now = timezone.now()
        
        # Получаем все активные обращения
        active_complaints = Complaint.objects.filter(
            status__in=['new', 'in_progress']
        ).select_related('user', 'department')
        
        for complaint in active_complaints:
            # Определяем срок выполнения
            deadline = complaint.created_at + self.priority_deadlines[complaint.priority]
            
            # Если срок истек
            if now > deadline and complaint.status != 'overdue':
                # Обновляем статус
                complaint.status = 'overdue'
                complaint.save()
                
                # Создаем уведомление
                Notification.objects.create(
                    user=complaint.user,
                    complaint=complaint,
                    type='deadline',
                    message=f"⚠️ Срок выполнения обращения #{complaint.id} истек!\n"
                           f"Категория: {complaint.department.name}\n"
                           f"Статус: Просрочено"
                )
                
                # Обновляем KPI управления
                kpi, _ = DepartmentKPI.objects.get_or_create(
                    department=complaint.department,
                    period=now.strftime('%Y-%m')
                )
                kpi.overdue_complaints += 1
                kpi.save()
            
            # Если срок истекает через день
            elif deadline - now <= timedelta(days=1) and not Notification.objects.filter(
                complaint=complaint,
                type='deadline',
                created_at__gte=now - timedelta(days=1)
            ).exists():
                # Создаем уведомление
                Notification.objects.create(
                    user=complaint.user,
                    complaint=complaint,
                    type='deadline',
                    message=f"⏰ Напоминание: срок выполнения обращения #{complaint.id} истекает через день!\n"
                           f"Категория: {complaint.department.name}\n"
                           f"Статус: {complaint.get_status_display()}"
                )

    @sync_to_async
    def update_kpi(self) -> None:
        """
        Обновляет KPI управлений
        """
        from .models import Department, DepartmentKPI, Complaint
        from django.utils import timezone
        from django.db.models import Count, Avg
        from datetime import timedelta
        
        now = timezone.now()
        period = now.strftime('%Y-%m')
        
        for department in Department.objects.all():
            # Получаем статистику за текущий период
            complaints = Complaint.objects.filter(
                department=department,
                created_at__year=now.year,
                created_at__month=now.month
            )
            
            total = complaints.count()
            completed = complaints.filter(status='completed').count()
            overdue = complaints.filter(status='overdue').count()
            
            # Рассчитываем среднее время выполнения
            completed_complaints = complaints.filter(status='completed')
            avg_completion_time = completed_complaints.aggregate(
                avg_time=Avg('completed_at' - 'created_at')
            )['avg_time']
            
            # Рассчитываем удовлетворенность (на основе времени выполнения)
            satisfaction_rate = 0.0
            if total > 0:
                on_time = completed_complaints.filter(
                    completed_at__lte=models.F('created_at') + self.priority_deadlines['medium']
                ).count()
                satisfaction_rate = (on_time / total) * 100
            
            # Обновляем или создаем KPI
            kpi, _ = DepartmentKPI.objects.get_or_create(
                department=department,
                period=period
            )
            
            kpi.total_complaints = total
            kpi.completed_complaints = completed
            kpi.overdue_complaints = overdue
            kpi.average_completion_time = avg_completion_time
            kpi.satisfaction_rate = satisfaction_rate
            kpi.save() 