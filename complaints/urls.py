from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.complaint_list, name='complaint_list'),
    path('<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('register/', views.register, name='register'),
] 