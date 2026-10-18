from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import Authentication, Notification
from authentication.permissions import *
from customers.models import Customers
from tickets.models import Tickets
from .serializers import TicketsSerializer


class TicketsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get(self, request):
        # Customers only see their own tickets
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile:
                customer_profile = Customers.objects.filter(user=request.user).first()

            if customer_profile:
                tickets = Tickets.objects.filter(customer=customer_profile)
            else:
                tickets = Tickets.objects.none()
        else:
            # Admins and Technicians see all tickets
            tickets = Tickets.objects.all()

        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TicketsCreate(APIView):
    permission_classes = [AdminPermission | CustomerPermission]

    def post(self, request):
        data = request.data.copy()

        # Automatically attach Customer profile if logged in as Customer
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile:
                customer_profile, _ = Customers.objects.get_or_create(
                    user=request.user,
                    defaults={'address': 'Not specified'}
                )
            data['customer'] = customer_profile.id

        serializer = TicketsSerializer(data=data)
        if serializer.is_valid():
            ticket = serializer.save()

            # Trigger notification for admins on new ticket submission
            admin_users = Authentication.objects.filter(role=Authentication.ROLE_CHOICES.ADMIN)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="New Ticket Submitted",
                    message=f"Ticket #{ticket.id} '{ticket.problem_title}' submitted by {request.user.username}."
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketsUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def put(self, request, pk):
        ticket = get_object_or_404(Tickets, id=pk)

        # Ensure customer owns the ticket
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile or ticket.customer_id != customer_profile.id:
                return Response(
                    {'message': 'You do not have permission to update this ticket.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TicketsSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            updated_ticket = serializer.save()

            # Notify the customer if a technician/admin updates their ticket status
            if request.user.role != Authentication.ROLE_CHOICES.CUSTOMER and ticket.customer and ticket.customer.user:
                Notification.objects.create(
                    user=ticket.customer.user,
                    title="Ticket Status Updated",
                    message=f"Your ticket #{ticket.id} status is now '{updated_ticket.status}'."
                )

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketsDelete(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def delete(self, request, pk):
        ticket = get_object_or_404(Tickets, id=pk)

        # Ensure customer owns the ticket
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile or ticket.customer_id != customer_profile.id:
                return Response(
                    {'message': 'You do not have permission to delete this ticket.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        ticket_title = ticket.problem_title
        ticket.delete()

        # Send confirmation notification
        Notification.objects.create(
            user=request.user,
            title="Ticket Deleted",
            message=f"Ticket '{ticket_title}' was successfully deleted."
        )

        return Response(
            {'message': 'Ticket successfully deleted'},
            status=status.HTTP_200_OK
        )


class TicketsDetail(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)

        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile or ticket.customer_id != customer_profile.id:
                return Response(
                    {'message': 'You do not have permission to view this ticket.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TicketsSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)

        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile or ticket.customer_id != customer_profile.id:
                return Response(
                    {'message': 'You do not have permission to update this ticket.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = TicketsSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)

        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile or ticket.customer_id != customer_profile.id:
                return Response(
                    {'message': 'You do not have permission to delete this ticket.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        ticket_title = ticket.problem_title
        ticket.delete()

        Notification.objects.create(
            user=request.user,
            title="Ticket Deleted",
            message=f"Ticket '{ticket_title}' was successfully deleted."
        )

        return Response(
            {'message': 'Ticket successfully deleted'},
            status=status.HTTP_200_OK
        )