from rest_framework import serializers

from .models import Customers
from authentication.models import Authentication


class CustomersSerializer(serializers.ModelSerializer):
    address = serializers.CharField(write_only=True)
    class Meta:
        model = Authentication
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
            'role':{
                'read_only': True,
            }
        }

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        user = Authentication.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            role = Authentication.ROLE_CHOICES.CUSTOMER,
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            email = validated_data.get('email', ''),
        )

        Customers.objects.create(
            user = user,
            address = address_data,
        )
        return user

class CustomerListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source = 'user.first_name',read_only=True)
    last_name = serializers.CharField(source = 'user.last_name',read_only=True)
    email = serializers.CharField(source='user.email',read_only=True)

    class Meta:
        model = Customers
        fields = ['id', 'first_name', 'last_name', 'email', 'address']









