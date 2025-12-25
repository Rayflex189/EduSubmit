from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentRegisterForm, AssignmentForm
from .models import Assignment, Student

def register(request):
    form = StudentRegisterForm()
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    return render(request, 'submissions/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        matric_number = request.POST.get('matric_number')
        password = request.POST.get('password')
        user = authenticate(request, matric_number=matric_number, password=password)
        if user:
            login(request, user)
            return redirect('student_dashboard')
    return render(request, 'submissions/login.html')

@login_required
def student_dashboard(request):
    assignments = Assignment.objects.filter(student=request.user)
    return render(request, 'submissions/student_dashboard.html', {'assignments': assignments})

@login_required
def upload_assignment(request):
    form = AssignmentForm()
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.student = request.user
            assignment.save()
            return redirect('student_dashboard')
        else:
            # Add this to see what's wrong
            print("Form errors:", form.errors)  # Check console output
    return render(request, 'submissions/upload_assignment.html', {'form': form})
    
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')
    assignments = Assignment.objects.all()
    return render(request, 'submissions/admin_dashboard.html', {'assignments': assignments})

@login_required
def grade_assignment(request, assignment_id):
    if not request.user.is_staff:
        return redirect('student_dashboard')
    assignment = Assignment.objects.get(id=assignment_id)
    if request.method == 'POST':
        assignment.grade = request.POST.get('grade')
        assignment.feedback = request.POST.get('feedback')
        assignment.save()
        return redirect('admin_dashboard')
    return render(request, 'submissions/grade_assignment.html', {'assignment': assignment})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
