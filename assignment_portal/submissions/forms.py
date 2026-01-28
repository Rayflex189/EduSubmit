from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Faculty, Department, Level, Assignment
)


class UserRegistrationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]
    
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)
    full_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'full_name', 'user_type', 'password1', 'password2']


class StudentProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.all(), required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    level = forms.ModelChoiceField(queryset=Level.objects.all(), required=True)
    
    class Meta:
        model = StudentProfile
        fields = ['matric_number', 'faculty', 'department', 'level', 'admission_year', 'phone_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If faculty is selected, filter departments
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass


class LecturerProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.all(), required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    
    class Meta:
        model = LecturerProfile
        fields = ['staff_id', 'faculty', 'department', 'designation', 
                 'office_location', 'office_hours', 'phone_extension']


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class GradeAssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['grade', 'score', 'feedback', 'status']
