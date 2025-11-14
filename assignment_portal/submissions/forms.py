from django import forms
from .models import Student, Assignment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class StudentRegisterForm(UserCreationForm):
    class Meta:
        model = Student
        fields = ['matric_number', 'full_name', 'email', 'password1', 'password2']

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file']
