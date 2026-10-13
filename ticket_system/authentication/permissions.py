from rest_framework.permissions import BasePermission

from .models import Authentication


class RolePermission(BasePermission):
    role = None
    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == self.role)


class AdminPermission(RolePermission):
    role = Authentication.ROLE_CHOICES.ADMIN

    def has_object_permission(self, request, view, obj):
        return True


class TechnicianPermission(RolePermission):
    role = Authentication.ROLE_CHOICES.TECHNICIAN

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'customer_id'):
            return obj.assignments_set.filter(is_active=True, technicians__user=request.user).exists()
        if hasattr(obj, 'tickets_id'):
            return obj.is_active and obj.technicians.user_id == request.user.id
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return obj == request.user


class CustomerPermission(RolePermission):
    role = Authentication.ROLE_CHOICES.CUSTOMER

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'customer_id'):
            return obj.customer.user_id == request.user.id
        if hasattr(obj, 'tickets_id'):
            return obj.tickets.customer.user_id == request.user.id
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return obj == request.user
