from rest_framework.permissions import BasePermission
from .models import Authentication

class AdminPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.ADMIN

class TechnicianPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN

class CustomerPermission(BasePermission):
    message = "You do not have permission to perform this action"
    def has_permission(self, request, view):
        return request.user.role == Authentication.ROLE_CHOICES.CUSTOMER
