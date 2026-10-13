from rest_framework import serializers

from .models import Technicians
from authentication.models import Authentication


class TechniciansSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    password = serializers.CharField(write_only=True, required=False)
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
        password = validated_data.pop('password', None)
        specialization = validated_data.pop('specialization')
        availability_status = validated_data.pop('availability_status')

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

    def validate(self, attrs):
        user_data = attrs.get('user', {})
        username = user_data.get('username')
        if username:
            queryset = Authentication.objects.filter(username=username)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.user_id)
            if queryset.exists():
                raise serializers.ValidationError({'username': 'A user with that username already exists.'})
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'This field is required.'})
        return attrs


class TechnicianListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Technicians
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'specialization', 'availability_status']
