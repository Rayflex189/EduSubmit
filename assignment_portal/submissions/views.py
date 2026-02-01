from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import (
    UserRegistrationForm, StudentProfileForm, 
    LecturerProfileForm, AssignmentForm, GradeAssignmentForm, LecturerProfileForm
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


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            return '/student/dashboard/'
        elif hasattr(user, 'lecturer_profile'):
            return '/lecturer/dashboard/'
        elif user.is_superuser:
            return '/admin/'
        return '/'
    
    def form_valid(self, form):
        # Custom login logic if needed
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            
            # Set session timeout based on remember me
            if not self.request.POST.get('remember'):
                self.request.session.set_expiry(0)  # Browser session
            else:
                self.request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(self.request, f'Welcome back, {user.full_name}!')
            return redirect(self.get_success_url())
        
        return super().form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Or for function-based view:
def login_view(request):
    if request.user.is_authenticated:
        # Redirect based on user type
        if hasattr(request.user, 'student_profile'):
            return redirect('student_dashboard')
        elif hasattr(request.user, 'lecturer_profile'):
            return redirect('lecturer_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry based on remember me
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            
            messages.success(request, f'Welcome back, {user.full_name}!')
            
            # Redirect based on user type
            if hasattr(user, 'student_profile'):
                return redirect('submissions/student_dashboard')
            elif hasattr(user, 'lecturer_profile'):
                return redirect('submissions/lecturer_dashboard')
            elif user.is_superuser:
                return redirect('/admin/')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'submissions/login.html')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_type = request.POST.get('user_type', 'student')
        
        if user_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.user_type = user_type
            user.username = user_form.cleaned_data.get('email')  # Use email as username
            user.save()
            
            # Create appropriate profile based on user type
            if user_type == 'student':
                # Redirect to complete student profile
                request.session['new_user_id'] = user.id
                request.session['user_type'] = 'student'
                return redirect('complete_student_profile')
            
            elif user_type == 'lecturer':
                # Create lecturer profile
                lecturer_profile = LecturerProfile.objects.create(
                    user=user,
                    staff_id=request.POST.get('staff_id'),
                    designation=request.POST.get('designation', 'Lecturer')
                )
                user.is_staff = True  # Make lecturer a staff member
                user.save()
                
                # Auto-login and redirect
                login(request, user)
                messages.success(request, f'Welcome, {user.full_name}! Your lecturer account has been created.')
                return redirect('lecturer_dashboard')
        
        else:
            # Show form errors
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': user_form})

def complete_student_profile(request):
    user_id = request.session.get('new_user_id')
    if not user_id:
        return redirect('register')
    
    user = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        profile_form = StudentProfileForm(request.POST)
        if profile_form.is_valid():
            student_profile = profile_form.save(commit=False)
            student_profile.user = user
            student_profile.matric_number = user_form.cleaned_data.get('matric_number')  # From registration
            student_profile.save()
            
            # Clear session
            del request.session['new_user_id']
            del request.session['user_type']
            
            # Auto-login and redirect
            login(request, user)
            messages.success(request, f'Welcome, {user.full_name}! Your student profile is now complete.')
            return redirect('student_dashboard')
    else:
        profile_form = StudentProfileForm()
    
    context = {
        'user': user,
        'form': profile_form,
        'faculties': Faculty.objects.all(),
        'departments': Department.objects.all(),
        'levels': Level.objects.all()
    }
    
    return render(request, 'complete_student_profile.html', context)

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

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = request.user.student_profile
    
    # Get student's assignments
    assignments = Assignment.objects.filter(
        student=student
    ).select_related('course', 'course__lecturer__user')
    
    # Get student's current courses
    current_courses = Course.objects.filter(
        department=student.department,
        level=student.level,
        is_active=True
    ).select_related('lecturer__user')
    
    # Calculate statistics
    total_assignments = assignments.count()
    graded_assignments = assignments.filter(status='graded').count()
    pending_assignments = assignments.filter(status__in=['pending', 'under_review']).count()
    total_courses = current_courses.count()
    
    # Calculate completion percentage
    completed_courses = current_courses.filter(
        assignments__student=student,
        assignments__status='graded'
    ).distinct().count()
    completion_percentage = (completed_courses / total_courses * 100) if total_courses > 0 else 0
    
    # Calculate average grade
    graded_scores = assignments.filter(score__isnull=False).values_list('score', flat=True)
    average_grade = round(sum(graded_scores) / len(graded_scores), 1) if graded_scores else 'N/A'
    
    # Calculate submission rate
    total_possible_assignments = sum(course.assignments.count() for course in current_courses)
    submission_rate = (total_assignments / total_possible_assignments * 100) if total_possible_assignments > 0 else 0
    
    # Get recent assignments (last 5)
    recent_assignments = assignments.order_by('-date_uploaded')[:5]
    
    # Prepare performance data
    performance_data = {
        'average_grade': average_grade,
        'submission_rate': round(submission_rate),
        'pending_work': pending_assignments,
    }
    
    context = {
        'student': student,
        'assignments': assignments,
        'recent_assignments': recent_assignments,
        'courses': current_courses,
        'total_assignments': total_assignments,
        'graded_assignments': graded_assignments,
        'pending_assignments': pending_assignments,
        'total_courses': total_courses,
        'completion_percentage': round(completion_percentage),
        'performance_data': performance_data,
        'average_grade': average_grade,
        'submission_rate': round(submission_rate),
    }
    
    return render(request, 'student_dashboard.html', context)
    
@login_required
@user_passes_test(is_student)
def upload_assignment(request):
    student = request.user.student_profile
    
    # Get student's current courses
    current_courses = Course.objects.filter(
        department=student.department,
        level=student.level,
        is_active=True
    ).select_related('lecturer__user')
    
    # Get recent uploads
    recent_uploads = Assignment.objects.filter(
        student=student
    ).select_related('course').order_by('-date_uploaded')[:5]
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.student = student
            
            # Get selected course
            course_id = request.POST.get('course')
            if course_id:
                try:
                    course = Course.objects.get(id=course_id)
                    assignment.course = course
                except Course.DoesNotExist:
                    messages.error(request, 'Invalid course selected.')
                    return redirect('upload_assignment')
            
            # Set additional fields
            assignment.status = 'pending'
            assignment.date_uploaded = timezone.now()
            
            assignment.save()
            
            # Create notification for lecturer
            messages.success(
                request, 
                f'Assignment "{assignment.title}" uploaded successfully!'
            )
            
            # Clear any saved draft
            if 'assignment_draft' in request.session:
                del request.session['assignment_draft']
            
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm()
    
    context = {
        'student': student,
        'courses': current_courses,
        'recent_uploads': recent_uploads,
        'form': form,
    }
    
    return render(request, 'upload_assignment.html', context)


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
    
    # Get the assignment, ensuring it belongs to lecturer's courses
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        course__lecturer=lecturer
    )
    
    # Get status choices for template
    assignment_status_choices = Assignment._meta.get_field('status').choices
    
    if request.method == 'POST':
        grade = request.POST.get('grade', '').strip()
        score = request.POST.get('score', '').strip()
        feedback = request.POST.get('feedback', '').strip()
        status = request.POST.get('status', 'graded')
        
        if grade:
            # Update assignment
            assignment.grade = grade.upper()
            assignment.feedback = feedback
            assignment.status = status
            assignment.graded_by = lecturer
            assignment.graded_date = timezone.now()
            
            # Parse score if provided
            if score:
                try:
                    assignment.score = float(score)
                except ValueError:
                    assignment.score = None
            
            assignment.save()
            
            # Create notification for student
            messages.success(
                request, 
                f'Grade submitted successfully for {assignment.student.user.full_name}!'
            )
            
            # Redirect back to assignments list
            return redirect('lecturer_assignments')
        else:
            messages.error(request, 'Please enter a grade.')
    
    context = {
        'assignment': assignment,
        'assignment_status_choices': assignment_status_choices,
        'lecturer': lecturer,
    }
    
    return render(request, 'grade_assignment.html', context)


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
