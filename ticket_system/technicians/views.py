from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from technicians.models import Technicians
from technicians.serializers import TechniciansSerializer, TechnicianListSerializer
from authentication.permissions import AdminPermission, TechnicianPermission
from django.shortcuts import get_object_or_404


class TechnicianRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TechniciansSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TechnicianView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]

    def get(self, request):
        if request.user.role == 'ADMIN':
            technicians = Technicians.objects.select_related('user').all().order_by('id')
        else:
            technicians = Technicians.objects.select_related('user').filter(user=request.user)
        serializer = TechnicianListSerializer(technicians, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TechnicianUpdate(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]

    def put(self, request, pk):
        technician = get_object_or_404(Technicians, pk=pk)
        self.check_object_permissions(request, technician)

        serializer = TechniciansSerializer(technician, data=request.data, partial = True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TechnicianDelete(APIView):
    permission_classes = [AdminPermission]
    def delete(self, request, pk):
        tech = get_object_or_404(Technicians, pk=pk)
        self.check_object_permissions(request, tech)
        tech.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TechnicianDetail(APIView):
    permission_classes = [AdminPermission]
    def get_object(self, pk):
        try:
            return Technicians.objects.get(pk=pk)
        except Technicians.DoesNotExist:
            return None

    def get(self, request, pk):
        tech = self.get_object(pk)
        if tech is None:
            return Response(
                data = {"message" : "Technician does not exist"},
                status = status.HTTP_404_NOT_FOUND,
            )
        serializer = TechniciansSerializer(tech)
        return Response(serializer.data)

    def put(self, request, pk):
        tech = self.get_object(pk)
        if tech is None:
            return Response(
                data = {"message" : "Technician does not exist"},
                status = status.HTTP_404_NOT_FOUND,
            )
        serializer = TechniciansSerializer(tech, data=request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tech = self.get_object(pk)
        if tech is None:
            return Response(
                data = {"message" : "Technician does not exist"},
                status = status.HTTP_404_NOT_FOUND,
            )
        tech.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




