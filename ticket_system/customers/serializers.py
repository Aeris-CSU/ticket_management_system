from rest_framework import serializers

from .models import Customers
from technicians.models import Technicians

class CustomersSerializer(serializers.ModelSerializer):
    specialization = serializers.CharField(required=False)
    availability_status = serializers.CharField(required=False)
    address = serializers.CharField(write_only=True)
    class Meta:
        model = Technicians
        fields = '__all__'

    def create(self, validated_data):
        address_data = validated_data.pop('address')

        user = Technicians.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            email = validated_data.get('email', ''),
            contact_number = validated_data.get('contact_number', ''),
            is_customer = True,
            is_admin = False,
        )

        Customers.objects.create(
            user = user,
            address = address_data,
        )
        return user









