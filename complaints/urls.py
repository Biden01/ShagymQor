from django.urls import path
from . import views

urlpatterns = [
    path('', views.complaint_list, name='complaints'),
    path('<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('<int:complaint_id>/comment/', views.add_comment, name='add_comment'),
    # ... existing code ...
] 