from rest_framework import serializers
from .models import Authentication

class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authentication
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        authentication = Authentication.objects.create(**validated_data)
        authentication.password = password
        authentication.save()
        return authentication

    def update(self, instance, validated_data):
        password = validated_data.pop('password')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance
