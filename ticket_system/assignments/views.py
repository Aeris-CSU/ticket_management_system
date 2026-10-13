from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import AssignmentsSerializer
from .models import Assignments
from authentication.models import Authentication
from authentication.permissions import AdminPermission, CustomerPermission, TechnicianPermission
from django.shortcuts import get_object_or_404

class AssignmentsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]

    def get_queryset(self, request):
        queryset = Assignments.objects.select_related(
            'tickets__customer__user',
            'technicians__user',
        )
        if request.user.role == Authentication.ROLE_CHOICES.TECHNICIAN:
            queryset = queryset.filter(technicians__user=request.user)
        elif request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            queryset = queryset.filter(tickets__customer__user=request.user)
        return queryset.order_by('-assigned_at')

    def get(self, request):
        assignments = self.get_queryset(request)
        serializer = AssignmentsSerializer(assignments, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            return Response(
                {'detail': 'Customers cannot assign tickets.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = AssignmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignmentCreateView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def post(self, request):
        serializer = AssignmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignmentUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def put(self, request, pk):
        assign = get_object_or_404(Assignments, pk=pk)
        self.check_object_permissions(request, assign)
        serializer = AssignmentsSerializer(assign, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentDelete(APIView):
    permission_classes = [AdminPermission]
    def delete(self, request, pk):
        assign = get_object_or_404(Assignments, pk=pk)
        assign.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AssignmentsDetail(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]
    def get(self, request, pk):
        try:
            assignment = Assignments.objects.get(pk=pk)
        except Assignments.DoesNotExist:
            return Response(
                data = {"message" : "Assignment does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, assignment)
        serializer = AssignmentsSerializer(assignment)
        return Response(serializer.data)

    def put(self, request, pk):
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            return Response(
                {'detail': 'Customers cannot update assignments.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            assignment = Assignments.objects.get(pk=pk)
        except Assignments.DoesNotExist:
            return Response(
                data = {"message" : "Assignment does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, assignment)
        serializer = AssignmentsSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.role != Authentication.ROLE_CHOICES.ADMIN:
            return Response(
                {'detail': 'Only administrators can delete assignments.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            assignment = Assignments.objects.get(pk=pk)
        except Assignments.DoesNotExist:
            return Response(
                data = {"message" : "Assignment does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, assignment)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


