from rest_framework import permissions
from .models import UserRole

class IsAdminRole(permissions.BasePermission):
    """Allows access only to Admin role users or superusers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == UserRole.ADMIN or request.user.is_superuser))

class IsManagerOrAdmin(permissions.BasePermission):
    """Allows access to Managers, Admins, and superusers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in [UserRole.ADMIN, UserRole.MANAGER] or request.user.is_superuser
        ))

class IsDeveloper(permissions.BasePermission):
    """Allows access to Developers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role == UserRole.DEVELOPER or request.user.is_superuser
        ))

class IsQATester(permissions.BasePermission):
    """Allows access to QA Testers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role == UserRole.QA or request.user.is_superuser
        ))
