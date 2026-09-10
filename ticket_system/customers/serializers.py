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
            }
        }

    def create(self, validated_data):
        address_data = validated_data.pop('address')

        user = Authentication.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            email = validated_data.get('email', ''),
            is_customer = True,
            is_admin = False,
        )

        Customers.objects.create(
            user = user,
            address = address_data,
        )
        return user









