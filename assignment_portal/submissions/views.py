from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import (
    UserRegistrationForm, StudentProfileForm, 
    LecturerProfileForm, AssignmentForm, GradeAssignmentForm
)
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Assignment, Course, Faculty, Department
)

# ---------- Utility Functions ----------
def is_student(user):
    return hasattr(user, 'student_profile')

def is_lecturer(user):
    return hasattr(user, 'lecturer_profile')


# ---------- Authentication Views ----------
class CustomLoginView(LoginView):
    template_name = 'submissions/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            return '/student/dashboard/'
        elif hasattr(user, 'lecturer_profile'):
            return '/lecturer/dashboard/'
        elif user.is_superuser:
            return '/admin/'
        return '/'


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        
        if user_form.is_valid():
            user = user_form.save()
            user_type = user_form.cleaned_data.get('user_type')
            
            # Create appropriate profile based on user type
            if user_type == 'student':
                return redirect('complete_student_profile', user_id=user.id)
            elif user_type == 'lecturer':
                return redirect('complete_lecturer_profile', user_id=user.id)
            
            login(request, user)
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'submissions/register.html', {'form': user_form})


def complete_student_profile(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        profile_form = StudentProfileForm(request.POST)
        if profile_form.is_valid():
            student_profile = profile_form.save(commit=False)
            student_profile.user = user
            student_profile.save()
            
            # Authenticate and login
            login(request, user)
            return redirect('student_dashboard')
    else:
        profile_form = StudentProfileForm()
    
    return render(request, 'submissions/complete_student_profile.html', {
        'form': profile_form,
        'user': user
    })


def complete_lecturer_profile(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        profile_form = LecturerProfileForm(request.POST)
        if profile_form.is_valid():
            lecturer_profile = profile_form.save(commit=False)
            lecturer_profile.user = user
            lecturer_profile.save()
            
            # Make user staff and save
            user.is_staff = True
            user.save()
            
            # Authenticate and login
            login(request, user)
            return redirect('lecturer_dashboard')
    else:
        profile_form = LecturerProfileForm()
    
    return render(request, 'submissions/complete_lecturer_profile.html', {
        'form': profile_form,
        'user': user
    })


# ---------- Student Views ----------
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = request.user.student_profile
    assignments = Assignment.objects.filter(student=student).order_by('-date_uploaded')[:5]
    courses = Course.objects.filter(department=student.department, level=student.level)
    
    # Calculate statistics
    total_assignments = Assignment.objects.filter(student=student).count()
    pending_assignments = Assignment.objects.filter(student=student, status='pending').count()
    graded_assignments = Assignment.objects.filter(student=student, status='graded').count()
    
    context = {
        'student': student,
        'assignments': assignments,
        'courses': courses,
        'total_assignments': total_assignments,
        'pending_assignments': pending_assignments,
        'graded_assignments': graded_assignments,
    }
    
    return render(request, 'submissions/student_dashboard.html', context)


@login_required
@user_passes_test(is_student)
def upload_assignment(request):
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.student = student
            assignment.save()
            messages.success(request, 'Assignment uploaded successfully!')
            return redirect('student_dashboard')
    else:
        form = AssignmentForm()
    
    # Get courses available for student's level and department
    courses = Course.objects.filter(
        department=student.department,
        level=student.level
    )
    
    return render(request, 'submissions/upload_assignment.html', {
        'form': form,
        'student': student,
        'courses': courses
    })


@login_required
@user_passes_test(is_student)
def student_assignments(request):
    student = request.user.student_profile
    assignments = Assignment.objects.filter(student=student).order_by('-date_uploaded')
    
    return render(request, 'submissions/student_assignments.html', {
        'assignments': assignments,
        'student': student
    })


@login_required
@user_passes_test(is_student)
def student_profile(request):
    student = request.user.student_profile
    
    if request.method == 'POST':
        # Handle profile updates here
        pass
    
    return render(request, 'submissions/student_profile.html', {
        'student': student
    })


# ---------- Lecturer Views ----------
@login_required
@user_passes_test(is_lecturer)
def lecturer_dashboard(request):
    lecturer = request.user.lecturer_profile
    
    # Get lecturer's courses
    courses = Course.objects.filter(lecturer=lecturer).prefetch_related('students')
    
    # Get assignments for lecturer's courses
    assignments = Assignment.objects.filter(
        course__lecturer=lecturer
    ).select_related('student__user', 'course', 'graded_by__user')
    
    # Calculate statistics
    total_assignments = assignments.count()
    graded_assignments = assignments.filter(status='graded').count()
    pending_assignments = assignments.filter(status__in=['pending', 'under_review']).count()
    total_courses = courses.count()
    
    # Get recent assignments (last 10)
    recent_assignments = assignments.order_by('-date_uploaded')[:10]
    
    # Get assignments with upcoming deadlines (within next 7 days)
    from datetime import datetime, timedelta
    next_week = datetime.now() + timedelta(days=7)
    upcoming_deadlines = assignments.filter(
        deadline__isnull=False,
        deadline__gte=datetime.now(),
        deadline__lte=next_week
    ).order_by('deadline')[:5]
    
    # Calculate course student counts
    for course in courses:
        course.student_count = StudentProfile.objects.filter(
            department=course.department,
            level=course.level
        ).count()
    
    context = {
        'lecturer': lecturer,
        'courses': courses,
        'assignments': assignments,
        'recent_assignments': recent_assignments,
        'upcoming_deadlines': upcoming_deadlines,
        'total_assignments': total_assignments,
        'graded_assignments': graded_assignments,
        'pending_assignments': pending_assignments,
        'total_courses': total_courses,
    }
    
    return render(request, 'lecturer_dashboard.html', context)


@login_required
@user_passes_test(is_lecturer)
def lecturer_assignments(request):
    lecturer = request.user.lecturer_profile
    status_filter = request.GET.get('status', 'all')
    
    assignments = Assignment.objects.filter(course__lecturer=lecturer)
    
    if status_filter != 'all':
        assignments = assignments.filter(status=status_filter)
    
    assignments = assignments.select_related('student', 'course').order_by('-date_uploaded')
    
    return render(request, 'submissions/lecturer_assignments.html', {
        'assignments': assignments,
        'lecturer': lecturer,
        'status_filter': status_filter
    })


@login_required
@user_passes_test(is_lecturer)
def grade_assignment(request, assignment_id):
    lecturer = request.user.lecturer_profile
    assignment = get_object_or_404(
        Assignment, 
        id=assignment_id,
        course__lecturer=lecturer
    )
    
    if request.method == 'POST':
        form = GradeAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.graded_by = lecturer
            assignment.save()
            messages.success(request, 'Assignment graded successfully!')
            return redirect('lecturer_assignments')
    else:
        form = GradeAssignmentForm(instance=assignment)
    
    return render(request, 'submissions/grade_assignment.html', {
        'form': form,
        'assignment': assignment,
        'lecturer': lecturer
    })


@login_required
@user_passes_test(is_lecturer)
def lecturer_courses(request):
    lecturer = request.user.lecturer_profile
    courses = Course.objects.filter(lecturer=lecturer).select_related('department', 'level')
    
    return render(request, 'submissions/lecturer_courses.html', {
        'courses': courses,
        'lecturer': lecturer
    })


@login_required
@user_passes_test(is_lecturer)
def lecturer_students(request):
    lecturer = request.user.lecturer_profile
    # Get students from lecturer's courses
    courses = Course.objects.filter(lecturer=lecturer)
    students = StudentProfile.objects.filter(
        department=lecturer.department
    ).distinct()
    
    return render(request, 'submissions/lecturer_students.html', {
        'students': students,
        'lecturer': lecturer
    })


# ---------- API Views ----------
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

# Create separate API apps for students and lecturers
# students/api/views.py
class StudentViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'student_profile'):
            return self.queryset.filter(user=self.request.user)
        elif hasattr(self.request.user, 'lecturer_profile'):
            # Lecturers can see their department's students
            return self.queryset.filter(department=self.request.user.lecturer_profile.department)
        return self.queryset.none()
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        student = self.get_object()
        assignments = Assignment.objects.filter(student=student)
        # Return serialized assignments
        return Response([])


# lecturers/api/views.py
class LecturerViewSet(viewsets.ModelViewSet):
    queryset = LecturerProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'lecturer_profile'):
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        lecturer = self.get_object()
        courses = Course.objects.filter(lecturer=lecturer)
        # Return serialized courses
        return Response([])


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
