from rest_framework.permissions import BasePermission
from .models import Authentication

class AdminPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == Authentication.ROLE_CHOICES.ADMIN
        )

    def has_object_permission(self, request, view, obj):
        return True

class TechnicianPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == Authentication.ROLE_CHOICES.TECHNICIAN
        )

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'technicians'):
            return obj.technicians.user == request.user
        if hasattr(obj, 'assignments_set'):
            return obj.assignments_set.filter(technicians__user=request.user).exists()
        return obj == request.user

class CustomerPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == Authentication.ROLE_CHOICES.CUSTOMER
        )

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            return obj.customer.user == request.user
        if hasattr(obj, 'tickets'):
            return obj.tickets.customer.user == request.user
        return obj == request.user
