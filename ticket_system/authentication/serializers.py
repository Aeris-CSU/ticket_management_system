from rest_framework import serializers
from .models import Authentication

class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authentication
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True},
                        'role': {'read_only': True}}

    def create(self, validated_data):
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
        password = validated_data.pop('password')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance
