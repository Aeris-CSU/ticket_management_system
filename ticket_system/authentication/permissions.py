from rest_framework.permissions import BasePermission
from .models import Authentication

class AdminPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.ADMIN

    def has_object_permission(self, request, view, obj):
        return True

class TechnicianPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN

    def has_object_permission(self, request, view, obj):
        target_user = obj.user if hasattr(obj, 'user') else obj
        return target_user == request.user

class CustomerPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.CUSTOMER

    def has_object_permission(self, request, view, obj):
        target_user = obj.user if hasattr(obj, 'user') else obj
        return target_user == request.user