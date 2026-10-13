from rest_framework import serializers
from .models import Authentication

class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authentication
        fields = [
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'role',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'role': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def create(self, validated_data):
        if not validated_data.get('password'):
            raise serializers.ValidationError({'password': 'This field is required.'})

        user = Authentication.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            role = Authentication.ROLE_CHOICES.ADMIN,
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            email = validated_data.get('email', ''),
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def validate_username(self, value):
        queryset = Authentication.objects.filter(username=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value
