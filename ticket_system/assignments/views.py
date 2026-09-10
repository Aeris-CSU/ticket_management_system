from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TicketsSerializer
from .models import Tickets
from rest_framework.permissions import AllowAny
from technicians.permissions import isAdmin

class AssignmentsView(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        tickets = Tickets.objects.all()
        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data)

class AssignmentCreateView(APIView):
    permissions_classes = (isAdmin,)
    serializer_class = TicketsSerializer
    def post(self, request):
        serializer = TicketsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
