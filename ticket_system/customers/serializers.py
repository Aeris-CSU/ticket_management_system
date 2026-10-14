from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from .models import Customers
from authentication.models import Authentication


class CustomersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    password = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(source='user.first_name', required=False, default='')
    last_name = serializers.CharField(source='user.last_name', required=False, default='')
    email = serializers.EmailField(source='user.email', required=False, default='')

    class Meta:
        model = Customers
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'address', 'contact_number']

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = validated_data.pop('password', None)
        address_data = validated_data.pop('address')

        user = Authentication.objects.create_user(
            username=user_data['username'],
            password=password,
            role=Authentication.ROLE_CHOICES.CUSTOMER,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            email=user_data.get('email', ''),
        )

        customer = Customers.objects.create(
            user=user,
            address=address_data,
            contact_number=validated_data.get('contact_number', ''),
        )
        return customer

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
        password = attrs.get('password')
        if password:
            try:
                validate_password(password, self.instance.user if self.instance else None)
            except Exception as exc:
                raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs


class CustomerListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Customers
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'address', 'contact_number']
