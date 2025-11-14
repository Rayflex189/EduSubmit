from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('upload/', views.upload_assignment, name='upload_assignment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('grade/<int:assignment_id>/', views.grade_assignment, name='grade_assignment'),
]
