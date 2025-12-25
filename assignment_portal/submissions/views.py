from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentRegisterForm, AssignmentForm
from .models import Assignment, Student
from django.contrib import messages

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
    # Get assignments for the current student
    assignments = Assignment.objects.filter(student=request.user)
    
    # Calculate statistics based on your model
    total_assignments = assignments.count()
    
    # Since your model doesn't have 'status', we'll use grade presence as indicator
    graded_count = assignments.exclude(grade__isnull=True).exclude(grade__exact='').count()
    pending_count = total_assignments - graded_count
    
    context = {
        'assignments': assignments,
        'student': request.user,  # This is your Student model instance
        'submitted': total_assignments,
        'pending': pending_count,
        'graded': graded_count,
    }
    
    return render(request, 'submissions/student_dashboard.html', context)
    
@login_required
def upload_assignment(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.student = request.user  # This will be your Student instance
            assignment.save()
            return redirect('student_dashboard')
    else:
        form = AssignmentForm()
    
    # Pass student object to template
    context = {
        'form': form,
        'student': request.user  # Add this line
    }
    
    return render(request, 'submissions/upload_assignment.html', context)
    
@login_required
def admin_dashboard(request):
    # Check if user is staff (lecturer/admin)
    if not request.user.is_staff:
        return redirect('student_dashboard')
    
    # Get all assignments with student details
    assignments = Assignment.objects.select_related('student').all()
    
    return render(request, 'submissions/admin_dashboard.html', {'assignments': assignments})

@login_required
def grade_assignment(request, assignment_id):
    if not request.user.is_staff:
        return redirect('student_dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        
        if grade:
            assignment.grade = grade
            assignment.feedback = feedback
            assignment.save()
            messages.success(request, f'Grade submitted successfully for {assignment.student.full_name}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please enter a grade.')
    
    return render(request, 'submissions/grade_assignment.html', {'assignment': assignment})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
