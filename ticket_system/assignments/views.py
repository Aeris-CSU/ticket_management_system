from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import Authentication
from authentication.permissions import AdminPermission, CustomerPermission, TechnicianPermission
from tickets.models import Tickets
from .models import Assignments
from .serializers import AssignmentsSerializer


class AssignmentBase(APIView):
    def get_assignment(self, pk):
        return get_object_or_404(Assignments.objects.select_related('tickets__customer__user', 'technicians__user'), pk=pk)

    def deactivate(self, assignment):
        with transaction.atomic():
            ticket = Tickets.objects.select_for_update().get(pk=assignment.tickets_id)
            assignment = Assignments.objects.select_for_update().get(pk=assignment.pk)
            if not assignment.is_active:
                return Response({'detail': 'Assignment is already inactive.'}, status=status.HTTP_409_CONFLICT)
            if ticket.status != Tickets.Status.ASSIGNED:
                return Response({'detail': 'Only assigned tickets can be unassigned. Reassign or resolve ongoing tickets.'}, status=status.HTTP_409_CONFLICT)
            assignment.is_active = False
            assignment.save(update_fields=['is_active'])
            ticket.status = Tickets.Status.OPEN
            ticket.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignmentsView(AssignmentBase):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get_queryset(self, request):
        qs = Assignments.objects.select_related('tickets__customer__user', 'technicians__user')
        if request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN:
            qs = qs.filter(is_active=True, technicians__user=request.user)
        elif request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            qs = qs.filter(tickets__customer__user=request.user)
        return qs.order_by('-assigned_at')

    def get(self, request):
        return Response(AssignmentsSerializer(self.get_queryset(request), many=True).data)

    def post(self, request):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            raise PermissionDenied('Only administrators can assign technicians.')
        serializer = AssignmentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(AssignmentsSerializer(serializer.save()).data, status=status.HTTP_201_CREATED)


class AssignmentCreateView(AssignmentsView):
    pass


class AssignmentUpdate(AssignmentBase):
    permission_classes = [AdminPermission]

    def put(self, request, pk):
        assignment = self.get_assignment(pk)
        serializer = AssignmentsSerializer(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(AssignmentsSerializer(serializer.save()).data)


class AssignmentDelete(AssignmentBase):
    permission_classes = [AdminPermission]

    def delete(self, request, pk):
        return self.deactivate(self.get_assignment(pk))


class AssignmentsDetail(AssignmentBase):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get(self, request, pk):
        assignment = self.get_assignment(pk)
        self.check_object_permissions(request, assignment)
        return Response(AssignmentsSerializer(assignment).data)

    def put(self, request, pk):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            raise PermissionDenied('Only administrators can reassign technicians.')
        assignment = self.get_assignment(pk)
        serializer = AssignmentsSerializer(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(AssignmentsSerializer(serializer.save()).data)

    def delete(self, request, pk):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            raise PermissionDenied('Only administrators can unassign technicians.')
        return self.deactivate(self.get_assignment(pk))
