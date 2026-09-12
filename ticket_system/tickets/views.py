from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from tickets.models import Tickets
from .serializers import TicketsSerializer
from technicians.permissions import isAdmin
from rest_framework.permissions import AllowAny, IsAuthenticated
from customers.permissions import isAuthenticatedUser
from authentication.permissions import *



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
