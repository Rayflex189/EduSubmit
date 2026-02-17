from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
import os  # Added for file validation
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Faculty, Department, Level, Assignment
)


class UserRegistrationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_user_type'
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
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your university email'
        })
    )
    
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Choose a username'
        })
    )
    
    matric_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Matric number (for students only)'
        })
    )
    
    staff_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Staff ID (for lecturers only)'
        })
    )
    
    designation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Designation (for lecturers only)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'full_name', 'user_type', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserProfile.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = self.data.get('user_type', '')
        
        if user_type == 'student':
            matric_number = cleaned_data.get('matric_number')
            if not matric_number:
                self.add_error('matric_number', 'Matric number is required for students.')
            elif StudentProfile.objects.filter(matric_number=matric_number).exists():
                self.add_error('matric_number', 'This matric number is already registered.')
        
        elif user_type == 'lecturer':
            staff_id = cleaned_data.get('staff_id')
            designation = cleaned_data.get('designation')
            
            if not staff_id:
                self.add_error('staff_id', 'Staff ID is required for lecturers.')
            elif LecturerProfile.objects.filter(staff_id=staff_id).exists():
                self.add_error('staff_id', 'This staff ID is already registered.')
            
            if not designation:
                self.add_error('designation', 'Designation is required for lecturers.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data['user_type']
        user.full_name = self.cleaned_data['full_name']
        
        if commit:
            user.save()
            # Create profile based on user type
            if user.user_type == 'student':
                StudentProfile.objects.create(
                    user=user,
                    matric_number=self.cleaned_data.get('matric_number', '')
                )
            elif user.user_type == 'lecturer':
                LecturerProfile.objects.create(
                    user=user,
                    staff_id=self.cleaned_data.get('staff_id', ''),
                    designation=self.cleaned_data.get('designation', 'Lecturer')
                )
                user.is_staff = True
                user.save()
        
        return user


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
        initial=True,
        label=_('Remember me'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
    )


class StudentProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=True,
        empty_label="Select Faculty",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_faculty'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="Select Department",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_department'
        })
    )
    
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        required=True,
        empty_label="Select Level",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_level'
        })
    )
    
    class Meta:
        model = StudentProfile
        fields = ['faculty', 'department', 'level', 'admission_year', 'phone_number']  # Changed from 'phone' to 'phone_number'
        widgets = {
            'admission_year': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 2023',
                'min': '2000',
                'max': '{% now "Y" %}'
            }),
            'phone_number': forms.TextInput(attrs={  # Changed from 'phone' to 'phone_number'
                'class': 'form-input',
                'placeholder': 'Phone number'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter departments based on selected faculty
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass


class LecturerProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=True,
        empty_label="Select Faculty",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="Select Department",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = LecturerProfile
        fields = ['staff_id', 'faculty', 'department', 'designation', 
                 'office', 'phone', 'bio']
        widgets = {
            'staff_id': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Staff ID'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Professor, Lecturer'
            }),
            'office': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Office location'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Brief bio',
                'rows': 4
            }),
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file', 'deadline']
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
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (20MB)
            max_size = 20 * 1024 * 1024  # 20MB
            if file.size > max_size:
                raise forms.ValidationError("File size must not exceed 20MB.")
            
            # Validate file type
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.rar']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        return file


class GradeAssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['grade', 'score', 'feedback', 'status']
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Provide feedback to the student'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }