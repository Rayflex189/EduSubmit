from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Faculty, Department, Level, Assignment
)
from django.utils.translation import gettext_lazy as _


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Optional description',
                'rows': 4
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'file-input'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (20MB)
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError("File size must not exceed 20MB.")
            
            # Validate file type
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.zip', '.rar']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        return file

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your university email'
        })
    )
    
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full name'
        })
    )
    
    matric_number = forms.CharField(
        max_length=20,
        required=False,  # Not required for lecturers
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter matric number'
        })
    )
    
    staff_id = forms.CharField(
        max_length=20,
        required=False,  # Not required for students
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter staff ID'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['email', 'full_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = self.data.get('user_type')
        
        if user_type == 'student':
            matric_number = cleaned_data.get('matric_number')
            if not matric_number:
                self.add_error('matric_number', 'Matric number is required for students.')
            elif StudentProfile.objects.filter(matric_number=matric_number).exists():
                self.add_error('matric_number', 'This matric number is already registered.')
        
        elif user_type == 'lecturer':
            staff_id = cleaned_data.get('staff_id')
            if not staff_id:
                self.add_error('staff_id', 'Staff ID is required for lecturers.')
            elif LecturerProfile.objects.filter(staff_id=staff_id).exists():
                self.add_error('staff_id', 'This staff ID is already registered.')
        
        return cleaned_data

class StudentProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = StudentProfile
        fields = ['faculty', 'department', 'level', 'admission_year', 'phone_number']
        widgets = {
            'admission_year': forms.NumberInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
        }

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_('Username or Email'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    
    remember = forms.BooleanField(
        required=False,
        label=_('Remember me'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
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
