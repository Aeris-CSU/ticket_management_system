from rest_framework import serializers

from .models import Technicians
from authentication.models import Authentication

class TechniciansSerializer(serializers.ModelSerializer):
    specialization = serializers.CharField(required=True, write_only=True)
    availability_status = serializers.CharField(required=True, write_only=True)
    contact_number = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Authentication
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'role' : {'read_only': True},
        }

    def create(self, validated_data):
        specialization = validated_data.pop('specialization')
        availability_status = validated_data.pop('availability_status')

        user = Authentication.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role = Authentication.ROLE_CHOICES.TECHNICIAN,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
        )

        Technicians.objects.create(
            user=user,
            specialization=specialization,
            availability_status=availability_status,
        )
        return user

class TechnicianListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source = 'user.first_name' ,read_only=True)
    last_name = serializers.CharField(source = 'user.last_name' ,read_only=True)
    email = serializers.CharField(source='user.email' ,read_only=True)
    class Meta:
        model = Technicians
        fields = ['id', 'first_name', 'last_name', 'email', 'specialization', 'availability_status']
