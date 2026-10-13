from .models import Customers
from .serializers import CustomersSerializer, CustomerListSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.models import Authentication
from authentication.permissions import AdminPermission, CustomerPermission, TechnicianPermission
from django.shortcuts import get_object_or_404

class CustomersView(APIView):
    permission_classes = [AdminPermission | TechnicianPermission | CustomerPermission]
    def get(self, request):
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            customers = Customers.objects.select_related('user').filter(user=request.user)
        else:
            customers = Customers.objects.select_related('user').all().order_by('id')
        serializer = CustomerListSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            return Response(
                {'detail': 'Customers cannot create other customer accounts.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CustomersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = [AdminPermission | TechnicianPermission]
    def post(self, request):
        serializer = CustomersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomersDetail(APIView):
    permission_classes = [AdminPermission | CustomerPermission | TechnicianPermission]

    def get(self, request, pk):
        try:
            customer = Customers.objects.get(pk=pk)
        except Customers.DoesNotExist:
            return Response(
                data = {"message" : "Customer does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )

        if request.user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            self.check_object_permissions(request, customer)
        serializer = CustomersSerializer(customer)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            customer = Customers.objects.get(pk=pk)
        except Customers.DoesNotExist:
            return Response(
                data = {"message" : "Customer does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, customer)
        serializer = CustomersSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            customer = Customers.objects.get(pk=pk)
        except Customers.DoesNotExist:
            return Response(
                data = {"message" : "Customer does not exist"},
                status = status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, customer)
        customer.delete()
        return Response(
            data = {"message" : "Customer deleted"},
            status = status.HTTP_204_NO_CONTENT
        )
