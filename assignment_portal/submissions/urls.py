from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.utils.functional import SimpleLazyObject
from . import views
from .admin import LecturerAdminSite

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

    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# Add this at the BOTTOM of your urls.py AFTER successful migrations
import sys

# Only add lecturer URLs if we're not running migrations
if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    try:
        from .models import LecturerProfile
        
        def _get_lecturer_admin_urls():
            """Inner function that queries the database - only called when needed"""
            urls = []
            for lecturer in LecturerProfile.objects.all():
                lecturer_site = LecturerAdminSite(lecturer, name=f'lecturer_{lecturer.staff_id}')
                # Register models on the site
                from .models import Course, Assignment
                from .admin import CourseAdmin, AssignmentAdmin
                lecturer_site.register(Course, CourseAdmin)
                lecturer_site.register(Assignment, AssignmentAdmin)
                urls.append(path(f'lecturer/{lecturer.staff_id}/admin/', lecturer_site.urls))
            return urls
        
        # Use SimpleLazyObject to delay execution until first access
        lecturer_urls = SimpleLazyObject(lambda: _get_lecturer_admin_urls())
        urlpatterns += lecturer_urls
    except Exception as e:
        print(f"Warning: Could not create lecturer admin URLs: {e}")
        # Continue without lecturer admin URLs