from rest_framework import serializers

from .models import Technicians
from authentication.models import Authentication


class TechniciansSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, default='')
    last_name = serializers.CharField(source='user.last_name', required=False, default='')
    email = serializers.EmailField(source='user.email', required=False, default='')

    class Meta:
        model = Technicians
        fields = [
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'specialization',
            'availability_status',
        ]

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = validated_data.pop('password')
        specialization = validated_data.pop('specialization')
        availability_status = validated_data.pop('availability_status')
        contact_number = validated_data.pop('contact_number', '')

        user = Authentication.objects.create_user(
            username=user_data['username'],
            password=password,
            role=Authentication.ROLE_CHOICES.TECHNICIAN,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            email=user_data.get('email', ''),
        )

        technician = Technicians.objects.create(
            user=user,
            specialization=specialization,
            availability_status=availability_status,
            contact_number=contact_number,
        )
        return technician

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        password = validated_data.pop('password', None)
        if password:
            user.set_password(password)

        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class TechnicianListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Technicians
        fields = ['id', 'first_name', 'last_name', 'email', 'specialization', 'availability_status', 'contact_number']