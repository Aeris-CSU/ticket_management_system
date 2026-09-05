from .models import Customers
from .serializers import CustomersSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

class CustomersView(APIView):
    def get(self, request):
        Customers = Customers.objects.all()
        serializer = CustomersSerializer(Customers, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CustomersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)