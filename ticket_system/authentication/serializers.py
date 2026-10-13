from rest_framework import serializers

from .models import Authentication


class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authentication
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = fields
