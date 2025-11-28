from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ---------- Custom User Manager ----------
class StudentManager(BaseUserManager):
    def create_user(self, matric_number, password=None, **extra_fields):
        if not matric_number:
            raise ValueError("Matric number is required")
        user = self.model(matric_number=matric_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matric_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(matric_number, password, **extra_fields)


# ---------- Custom User ----------
class Student(AbstractBaseUser, PermissionsMixin):
    matric_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # for admin access

    USERNAME_FIELD = 'matric_number'
    REQUIRED_FIELDS = []

    objects = StudentManager()

    def __str__(self):
        return self.matric_number


# ---------- Assignment Model ----------
class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = CloudinaryField('profile_pic', null=True, blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=5, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.student.matric_number}"
