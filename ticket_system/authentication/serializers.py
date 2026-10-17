from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import Authentication


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context['user']
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Your current password is incorrect.'})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        if attrs['new_password'] == attrs['current_password']:
            raise serializers.ValidationError({'new_password': 'Choose a different password.'})
        validate_password(attrs['new_password'], user)
        return attrs


class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authentication
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = fields
