from rest_framework import serializers
from .models import Tickets
from authentication.models import Authentication
from customers.models import Customers

class TicketsSerializer(serializers.ModelSerializer):
    VALID_STATUSES = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']

    customer_name = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(required=False)

    class Meta:
        model = Tickets
        fields = [
            'id',
            'problem_title',
            'problem_description',
            'status',
            'customer',
            'customer_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'customer_name', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        return f'{obj.customer.user.first_name} {obj.customer.user.last_name}'.strip() or obj.customer.user.username

    def validate_status(self, value):
        value = value.upper()
        if value not in self.VALID_STATUSES:
            raise serializers.ValidationError(
                f'Status must be one of: {", ".join(self.VALID_STATUSES)}.'
            )
        return value

    def validate_customer(self, value):
        request = self.context.get('request')
        if (
            request
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.CUSTOMER
            and value.user_id != request.user.id
        ):
            raise serializers.ValidationError('Customers can only create tickets for their own account.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if (
            request
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.CUSTOMER
            and 'status' in attrs
        ):
            raise serializers.ValidationError(
                {'status': 'Customers cannot set or update ticket status.'}
            )
        if (
            request
            and request.user.is_authenticated
            and request.user.role == Authentication.ROLE_CHOICES.CUSTOMER
            and not self.instance
            and 'customer' not in attrs
        ):
            try:
                attrs['customer'] = Customers.objects.get(user=request.user)
            except Customers.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {'customer': 'No customer profile is linked to this user.'}
                ) from exc
        return attrs

    def create(self, validated_data):
        validated_data.setdefault('status', 'OPEN')
        return super().create(validated_data)
