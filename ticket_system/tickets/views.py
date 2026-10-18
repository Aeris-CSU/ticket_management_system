from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import Authentication
from authentication.permissions import AdminPermission, CustomerPermission, TechnicianPermission
from assignments.models import Assignments
from assignments.services import release_technicians
from tickets.models import Tickets
from .serializers import TicketStatusSerializer, TicketsSerializer


class TicketsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get_queryset(self, request):
        queryset = Tickets.objects.select_related('customer__user').filter(deleted_at__isnull=True)
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            queryset = queryset.filter(customer__user=request.user)
        elif request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN:
            queryset = queryset.filter(assignments__is_active=True, assignments__technicians__user=request.user).distinct()
        return queryset.order_by('-created_at')

    def get(self, request):
        return Response(TicketsSerializer(self.get_queryset(request), many=True).data)

    def post(self, request):
        if request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN:
            raise PermissionDenied('Technicians cannot create tickets.')
        serializer = TicketsSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(TicketsSerializer(ticket).data, status=status.HTTP_201_CREATED)


class TicketsCreate(TicketsView):
    pass


class TicketDetailBase(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get_ticket(self, pk):
        return get_object_or_404(Tickets.objects.select_related('customer__user'), pk=pk, deleted_at__isnull=True)


class TicketsUpdate(TicketDetailBase):
    permission_classes = [AdminPermission | CustomerPermission]

    def put(self, request, pk):
        ticket = self.get_ticket(pk)
        self.check_object_permissions(request, ticket)
        serializer = TicketsSerializer(ticket, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(TicketsSerializer(serializer.save()).data)


class TicketsDelete(TicketDetailBase):
    permission_classes = [AdminPermission]

    def delete(self, request, pk):
        ticket = self.get_ticket(pk)
        if ticket.status in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
            ticket.deleted_at = timezone.now()
            ticket.save(update_fields=['deleted_at'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        if ticket.assignments_set.exists():
            return Response({'detail': 'Tickets with assignment history cannot be deleted.'}, status=status.HTTP_409_CONFLICT)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketsDetail(TicketDetailBase):
    def get(self, request, pk):
        ticket = self.get_ticket(pk)
        self.check_object_permissions(request, ticket)
        return Response(TicketsSerializer(ticket).data)

    def put(self, request, pk):
        if request.user.role not in (Authentication.ROLE_CHOICES.ADMIN, Authentication.ROLE_CHOICES.CUSTOMER):
            raise PermissionDenied('Technicians cannot edit ticket details.')
        return TicketsUpdate().put(request, pk)

    def delete(self, request, pk):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            raise PermissionDenied('Only administrators can delete tickets.')
        return TicketsDelete().delete(request, pk)


class TicketStatusUpdate(TicketDetailBase):
    def patch(self, request, pk):
        with transaction.atomic():
            ticket = get_object_or_404(Tickets.objects.select_for_update().select_related('customer__user'), pk=pk)
            if ticket.status in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
                raise ValidationError({'status': 'Resolved or cancelled tickets cannot be changed.'})

            role = request.user.role
            if role == Authentication.ROLE_CHOICES.TECHNICIAN:
                if not ticket.assignments_set.filter(is_active=True, technicians__user=request.user).exists():
                    raise PermissionDenied('Technicians can only update tickets currently assigned to them.')
            elif role == Authentication.ROLE_CHOICES.CUSTOMER and ticket.customer.user_id != request.user.id:
                raise PermissionDenied('Customers can only update their own tickets.')

            serializer = TicketStatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            new_status = serializer.validated_data['status']
            allowed = {
                Tickets.Status.OPEN: {Tickets.Status.CANCELLED},
                Tickets.Status.ASSIGNED: {Tickets.Status.ONGOING, Tickets.Status.CANCELLED},
                Tickets.Status.ONGOING: {Tickets.Status.RESOLVED, Tickets.Status.CANCELLED},
            }
            permitted = allowed.get(ticket.status, set())
            if role == Authentication.ROLE_CHOICES.TECHNICIAN:
                permitted = {
                    Tickets.Status.ASSIGNED: {Tickets.Status.ONGOING},
                    Tickets.Status.ONGOING: {Tickets.Status.RESOLVED},
                }.get(ticket.status, set())
            elif role == Authentication.ROLE_CHOICES.CUSTOMER:
                permitted = {Tickets.Status.CANCELLED} if ticket.status == Tickets.Status.OPEN else set()
            if new_status not in permitted:
                raise ValidationError({'status': f'Cannot transition a {ticket.status} ticket to {new_status}.'})

            reason = serializer.validated_data.get('cancellation_reason', '')
            if new_status == Tickets.Status.CANCELLED and role == Authentication.ROLE_CHOICES.ADMIN:
                if not reason:
                    raise ValidationError({'cancellation_reason': 'Explain why you are cancelling this ticket.'})
                ticket.cancellation_reason = reason
            elif reason:
                raise ValidationError({'cancellation_reason': 'Only administrators cancelling a ticket can provide a reason.'})

            ticket.status = new_status
            ticket.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
            if new_status in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
                technician_ids = list(Assignments.objects.filter(tickets=ticket, is_active=True).values_list('technicians_id', flat=True))
                Assignments.objects.filter(tickets=ticket, is_active=True).update(is_active=False)
                release_technicians(technician_ids)
        return Response(TicketsSerializer(ticket).data)
