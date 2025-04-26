from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Complaint, Department, MediaFile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

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

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Введите действующий email адрес'
    )
    first_name = forms.CharField(
        required=True,
        label='Имя',
        max_length=30,
        help_text='Введите ваше имя'
    )
    last_name = forms.CharField(
        required=True,
        label='Фамилия',
        max_length=30,
        help_text='Введите вашу фамилию'
    )
    username = forms.CharField(
        label='Имя пользователя',
        help_text='Придумайте уникальное имя пользователя',
        min_length=3,
        max_length=30
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
        help_text='Пароль должен содержать минимум 8 символов'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput,
        help_text='Введите пароль еще раз для подтверждения'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Это имя пользователя уже занято')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file', 'file_type']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'})
        } 