from authentication.models import Authentication
from .models import Customers
from .serializers import CustomersSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from technicians.permissions import isAdmin
from technicians.permissions import isAdmin
from rest_framework.permissions import AllowAny
from authentication.models import Authentication

class CustomersView(APIView):
    permission_classes = (isAdmin,)
    def get(self, request):
        customers = Authentication.objects.filter(is_customer=True)
        serializer = CustomersSerializer(customers, many=True)
        return Response(serializer.data)

class CustomersCreate(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = CustomersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)