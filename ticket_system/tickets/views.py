from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from tickets.models import Tickets
from .serializers import TicketsSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from authentication.permissions import *
from django.shortcuts import get_object_or_404


class TicketsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get(self, request):
        # Customers only see their own tickets
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile:
                from customers.models import Customers
                customer_profile = Customers.objects.filter(user=request.user).first()

            if customer_profile:
                tickets = Tickets.objects.filter(customer=customer_profile)
            else:
                tickets = Tickets.objects.none()
        else:
            # Admins and Technicians see all tickets
            tickets = Tickets.objects.all()

        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data)

class TicketsCreate(APIView):
    permission_classes = [AdminPermission | CustomerPermission]

    def post(self, request):
        data = request.data.copy()

        # If a Customer is logged in, attach their Customers profile ID automatically
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customer_profile = getattr(request.user, 'customers', None) or getattr(request.user, 'customer', None)
            if not customer_profile:
                # If no linked customer row exists yet, get or create it
                from customers.models import Customers
                customer_profile, _ = Customers.objects.get_or_create(
                    user=request.user,
                    defaults={'address': 'Not specified'}
                )
            data['customer'] = customer_profile.id

        serializer = TicketsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketsUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]

    def put(self, request, pk):
        ticket = Tickets.objects.get(id=pk)
        serializer = TicketsSerializer(ticket, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketsDelete(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def delete(self, request, pk):
        ticket = Tickets.objects.get(id=pk)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketsDetail(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            self.check_object_permissions(request, ticket)
        serializer = TicketsSerializer(ticket)
        return Response(serializer.data)

    def put(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)

        # 1. Enforce ownership check for customer updates
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            self.check_object_permissions(request, ticket)

        serializer = TicketsSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # 2. Return 400 Bad Request if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)

        # 3. Block customers from deleting tickets entirely
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            return Response(
                data={"message": "Customers are not allowed to delete tickets."},
                status=status.HTTP_403_FORBIDDEN
            )

        self.check_object_permissions(request, ticket)

        # 4. Perform actual database deletion
        ticket.delete()
        return Response(
            data={"message": "Ticket successfully deleted"},
            status=status.HTTP_204_NO_CONTENT
        )