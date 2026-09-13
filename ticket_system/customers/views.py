from authentication.models import Authentication
from .models import Customers
from .serializers import CustomersSerializer, CustomerListSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from authentication.models import Authentication
from authentication.permissions import *
from django.shortcuts import get_object_or_404

class CustomersView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission]
    def get(self, request):
        customers = Customers.objects.select_related('user').all()
        serializer = CustomerListSerializer(customers, many=True)
        return Response(serializer.data)


class CustomersUpdate(APIView):
    permission_classes = [AdminPermission | CustomerPermission]
    def put(self, request, pk):
        customer = get_object_or_404(Customers, pk=pk)
        self.check_object_permissions(request, customer)

        serializer = CustomersSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomersDelete(APIView):
    permission_classes = [AdminPermission | CustomerPermission]
    def delete(self, request, pk):
        customer = get_object_or_404(Customers, pk=pk)
        self.check_object_permissions(request, customer)
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class CustomersCreate(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = CustomersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)