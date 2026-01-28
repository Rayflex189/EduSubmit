from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model

# ---------- Base User Models ----------
class BaseUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Administrator'),
    ]
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = BaseUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"


# ---------- Academic Structure ----------
class Faculty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    head_of_department = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, 
                                          null=True, blank=True, related_name='headed_departments')
    
    class Meta:
        unique_together = ('faculty', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.faculty.code})"


class Level(models.Model):
    LEVELS = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
        ('600', '600 Level'),
    ]
    
    name = models.CharField(max_length=50, choices=LEVELS, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


# ---------- Student Profile ----------
class StudentProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    matric_number = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='students')
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    admission_year = models.IntegerField()
    phone_number = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.matric_number} - {self.user.full_name}"


# ---------- Lecturer Profile ----------
class LecturerProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='lecturers')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='lecturers')
    designation = models.CharField(max_length=100)
    office_location = models.CharField(max_length=100, blank=True)
    office_hours = models.TextField(blank=True)
    phone_extension = models.CharField(max_length=10, blank=True)
    is_department_head = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.staff_id} - {self.user.full_name}"


# ---------- Course Model ----------
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credit_units = models.IntegerField(default=3)
    deadline = models.DateTimeField(null=True, blank=True, help_text="Assignment submission deadline")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='courses')
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, 
                                related_name='courses_teaching')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.title}"


# ---------- Assignment Model ----------
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = CloudinaryField('file', null=True, blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)
    submission_date = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ], default='pending')
    grade = models.CharField(max_length=5, blank=True, null=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    graded_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_uploaded']
    
    def __str__(self):
        return f"{self.title} - {self.student.matric_number}"
