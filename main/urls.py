from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('complaints/', include('complaints.urls')),
    path('analytics/', views.analytics, name='analytics'),
] 