from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from tickets.models import Tickets
from .serializers import TicketsSerializer
from authentication.models import Authentication
from authentication.permissions import AdminPermission, CustomerPermission, TechnicianPermission
from django.shortcuts import get_object_or_404


class TicketsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get_queryset(self, request):
        queryset = Tickets.objects.select_related('customer__user').all()
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            queryset = queryset.filter(customer__user=request.user)
        elif request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN:
            queryset = queryset.filter(assignments__technicians__user=request.user).distinct()
        return queryset.order_by('-created_at')

    def get(self, request):
        tickets = self.get_queryset(request)
        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TicketsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketsCreate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]
    def post(self, request):
        serializer = TicketsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketsUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]

    def put(self, request, pk):
        ticket = get_object_or_404(Tickets, id=pk)
        self.check_object_permissions(request, ticket)
        serializer = TicketsSerializer(ticket, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketsDelete(APIView):
    permission_classes = [AdminPermission]
    def delete(self, request, pk):
        ticket = get_object_or_404(Tickets, id=pk)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TicketsDetail(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]
    def get(self, request, pk):
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            return Response(
                data = {"message" : "Ticket does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, ticket)
        serializer = TicketsSerializer(ticket)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            return Response(
                data = {"message" : "Ticket does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, ticket)
        serializer = TicketsSerializer(ticket, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            return Response(
                {'detail': 'Only administrators can delete tickets.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            return Response(
                data = {"message" : "Ticket does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, ticket)
        ticket.delete()
        return Response(
            data = {"message" : "Ticket successfully deleted"},
            status = status.HTTP_204_NO_CONTENT
        )


class TicketStatusUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]

    def patch(self, request, pk):
        ticket = get_object_or_404(Tickets, pk=pk)
        self.check_object_permissions(request, ticket)

        serializer = TicketsSerializer(
            ticket,
            data={'status': request.data.get('status')},
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
