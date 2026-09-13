from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from tickets.models import Tickets
from .serializers import TicketsSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from authentication.permissions import *
from django.shortcuts import get_object_or_404


class TicketsView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def get(self, request):
        tickets = Tickets.objects.all()
        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data)


class TicketsCreate(APIView):
    permission_classes = [AdminPermission | CustomerPermission]
    def post(self, request):
        serializer = TicketsSerializer(data=request.data)
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
