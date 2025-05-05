from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('status/', views.bot_status, name='bot_status'),
] 