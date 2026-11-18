from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    MANAGER = 'MANAGER', 'Project Manager'
    DEVELOPER = 'DEVELOPER', 'Developer'
    QA = 'QA', 'QA Tester'

class CustomUser(AbstractUser):
    """
    Custom user model supporting Role-Based Access Control (RBAC).
    Roles: ADMIN, MANAGER, DEVELOPER, QA
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DEVELOPER,
        help_text="Role determining platform permissions."
    )
    email = models.EmailField(unique=True, help_text="Required unique email address.")
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_admin_role(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    def is_manager_role(self):
        return self.role in (UserRole.ADMIN, UserRole.MANAGER) or self.is_superuser

    def is_developer_role(self):
        return self.role == UserRole.DEVELOPER

    def is_qa_role(self):
        return self.role == UserRole.QA

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
