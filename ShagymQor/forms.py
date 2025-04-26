from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Complaint, Department

class ComplaintForm(forms.ModelForm):
    """Форма для создания и редактирования жалобы"""
    class Meta:
        model = Complaint
        fields = ['department', 'status', 'assigned_to', 'priority', 'tags']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ComplaintFilterForm(forms.Form):
    """Форма для фильтрации жалоб"""
    STATUS_CHOICES = [
        ('', _('Все статусы')),
        ('new', _('Новые')),
        ('in_progress', _('В процессе')),
        ('completed', _('Выполненные')),
        ('overdue', _('Просроченные')),
    ]

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label=_('Все управления'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Поиск...')})
    )

class DepartmentForm(forms.ModelForm):
    """Форма для управления отделами"""
    class Meta:
        model = Department
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        } 