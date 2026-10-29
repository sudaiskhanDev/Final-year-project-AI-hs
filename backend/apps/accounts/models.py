from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for AI-Based Recruitment System.
    Extends Django's AbstractUser to get:
      - password hashing (built-in)
      - is_active, is_staff, is_superuser, date_joined, last_login
    Adds custom fields from ERD:
      - user_id (custom PK)
      - full_name
      - email (unique)
      - phone_no
      - role
      - created_at
    """

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("hr", "HR"),
        ("candidate", "Candidate"),
    )

    user_id = models.BigAutoField(primary_key=True)

    full_name = models.CharField(max_length=150)

    email = models.EmailField(unique=True)

    phone_no = models.CharField(max_length=20, blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="candidate",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # AbstractUser ka username field hata dete hain — hum email se login karenge
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "user"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.role}"





class HRProfile(models.Model):
    """
    HR Profile — sirf un users ke liye jinka role='hr'.
    Admin dashboard se HR banega, aur uske liye ye profile create hogi.
    """

    hr_id = models.BigAutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hr_profile",
        db_column="user_id",
    )


    department = models.CharField(max_length=100, blank=True, null=True)

    designation = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hr_profile"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} - {self.designation} ({self.department})"




class CandidateProfile(models.Model):
    """
    Candidate Profile — sirf un users ke liye jinka role='candidate'.
    Register ke baad candidate ye details bharta hai.
    """

    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )

    candidate_id = models.BigAutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
        db_column="user_id",
    )

    date_of_birth = models.DateField(blank=True, null=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )

    address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidate_profile"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} - Candidate"