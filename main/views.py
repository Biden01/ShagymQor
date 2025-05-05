from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm

def home(request):
    """Главная страница"""
    return render(request, 'main/home.html')

@login_required
def profile(request):
    """Страница профиля пользователя"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'main/profile.html', {'form': form})

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def about(request):
    """Страница о системе"""
    return render(request, 'main/about.html')

def contact(request):
    """Страница контактов"""
    return render(request, 'main/contact.html')

@login_required
def analytics(request):
    """Страница аналитики"""
    return render(request, 'main/analytics.html') 