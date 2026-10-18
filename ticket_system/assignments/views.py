#Assignments/View

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import AssignmentsSerializer
from .models import Assignments
from rest_framework.permissions import AllowAny
from authentication.permissions import *
from django.shortcuts import get_object_or_404

class AssignmentsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        tickets = Assignments.objects.all()
        serializer = AssignmentsSerializer(tickets, many=True)
        return Response(serializer.data)

class AssignmentCreateView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def post(self, request):
        serializer = AssignmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignmentUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def put(self, request, pk):
        assign = Assignments.objects.get(pk=pk)
        serializer = AssignmentsSerializer(assign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentDelete(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def delete(self, request, pk):
        assign = Assignments.objects.get(pk=pk)
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


