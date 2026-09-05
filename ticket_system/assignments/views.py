from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TicketsSerializer
from .models import Tickets

class AssignmentsView(APIView):
    def get(self, request):
        tickets = Tickets.objects.all()
        serializer = TicketsSerializer(tickets, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = TicketsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
