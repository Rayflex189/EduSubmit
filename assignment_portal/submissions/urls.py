this is the my submission app urls from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from . import views
from .admin import LecturerAdminSite

# Import all lecturer profiles to create their admin sites
# This would typically be done dynamically
from .models import LecturerProfile

urlpatterns = [
    path('', lambda request: redirect('login')),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/upload/', views.upload_assignment, name='upload_assignment'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/profile/', views.student_profile, name='student_profile'),
    
    # Lecturer URLs
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/assignments/', views.lecturer_assignments, name='lecturer_assignments'),
    path('lecturer/courses/', views.lecturer_courses, name='lecturer_courses'),
    path('lecturer/grade/<int:assignment_id>/', views.grade_assignment, name='grade_assignment'),
    path('lecturer/students/', views.lecturer_students, name='lecturer_students'),
    
    # API URLs
    #path('api/students/', include('students.api.urls')),
    #path('api/lecturers/', include('lecturers.api.urls')),
    
    # Admin URLs
    #path('admin/', admin.site.urls),
]

# Dynamically create lecturer admin URLs
def get_lecturer_admin_urls():
    urls = []
    for lecturer in LecturerProfile.objects.all():
        lecturer_site = LecturerAdminSite(lecturer, name=f'lecturer_{lecturer.staff_id}')
        urls.append(path(f'lecturer/{lecturer.staff_id}/admin/', lecturer_site.urls))
    return urls

urlpatterns += get_lecturer_admin_urls()