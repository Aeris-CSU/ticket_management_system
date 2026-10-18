from django.utils import timezone
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
from .services import release_technicians


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
            assignment.ended_at = timezone.now()
            assignment.end_reason = 'UNASSIGNED'
            assignment.save(update_fields=['is_active', 'ended_at', 'end_reason'])
            release_technicians([assignment.technicians_id])
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


class TechnicianHistory(APIView):
    permission_classes = [TechnicianPermission]

    def get(self, request, pk=None):
        from django.db.models import Q
        from rest_framework.pagination import PageNumberPagination
        from .serializers import AssignmentHistorySerializer
        query = Assignments.objects.select_related('tickets__customer__user').filter(
            technicians__user=request.user, is_active=False, tickets__deleted_at__isnull=True,
        ).order_by('-ended_at', '-created_at', '-id')
        if pk is not None:
            return Response(AssignmentHistorySerializer(get_object_or_404(query, pk=pk)).data)
        search = request.query_params.get('search', '').strip()
        for word in search.split():
            query = query.filter(Q(tickets__ticket_number__icontains=word) | Q(tickets__problem_title__icontains=word) | Q(tickets__customer__user__first_name__icontains=word) | Q(tickets__customer__user__last_name__icontains=word) | Q(tickets__customer__user__username__icontains=word))
        outcome = request.query_params.get('outcome', '')
        if outcome == 'PREVIOUS':
            query = query.filter(end_reason='')
        elif outcome:
            query = query.filter(end_reason=outcome)
        paginator = PageNumberPagination()
        paginator.page_size = 30
        page = paginator.paginate_queryset(query, request, view=self)
        return paginator.get_paginated_response(AssignmentHistorySerializer(page, many=True).data)
