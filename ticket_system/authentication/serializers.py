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
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile_picture', 'role', 'created_at', 'updated_at']
        read_only_fields = fields


class ProfilePictureSerializer(serializers.Serializer):
    profile_picture = serializers.ImageField()

    def validate_profile_picture(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Choose an image smaller than 5 MB.')
        from PIL import Image, ImageOps
        from django.core.files.base import ContentFile
        from io import BytesIO
        from uuid import uuid4
        try:
            value.seek(0)
            with Image.open(value) as original:
                if original.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError()
                if original.width > 4096 or original.height > 4096:
                    raise ValueError()
                image = ImageOps.exif_transpose(original).convert('RGB')
                image.thumbnail((512, 512))
                output = BytesIO()
                image.save(output, format='JPEG', quality=88)
            return ContentFile(output.getvalue(), name=f'{uuid4().hex}.jpg')
        except (ValueError, OSError, Image.DecompressionBombError):
            raise serializers.ValidationError('Choose a JPG, PNG, or WebP image up to 4096 by 4096 pixels.')
