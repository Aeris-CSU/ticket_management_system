from rest_framework.permissions import BasePermission
from .models import Authentication


class AdminPermission(BasePermission):
    message = "You do not have permission to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.ADMIN
        )

    def has_object_permission(self, request, view, obj):
        return True


class TechnicianPermission(BasePermission):
    message = "You do not have permission to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN
        )

    def has_object_permission(self, request, view, obj):
        target_user = obj.user if hasattr(obj, 'user') else obj
        return target_user == request.user


class CustomerPermission(BasePermission):
    message = "You do not have permission to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.CUSTOMER
        )

    def has_object_permission(self, request, view, obj):
        # Case 1: When checking a Ticket (obj has customer_id)
        if hasattr(obj, 'customer_id'):
            # Resolves whether customer_id is a ForeignKey (Customers instance) or a raw scalar ID
            ticket_customer_id = getattr(obj.customer_id, 'id', obj.customer_id)

            # Resolves the current logged-in user's customer ID
            # Checks user.customer_id, user.customer.id, or user.id
            user_customer = getattr(request.user, 'customer', None)
            user_customer_id = (
                    getattr(user_customer, 'id', None)
                    or getattr(request.user, 'customer_id', None)
                    or request.user.id
            )
            return ticket_customer_id == user_customer_id

        # Case 2: When checking a Customers model or User model directly
        target_user = obj.user if hasattr(obj, 'user') else obj
        return target_user == request.user