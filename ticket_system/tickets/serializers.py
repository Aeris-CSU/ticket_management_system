from rest_framework import serializers

from authentication.models import Authentication
from customers.models import Customers
from .models import Tickets


class TicketsSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customers.objects.select_related('user').all(), required=False)

    class Meta:
        model = Tickets
        fields = ['id', 'problem_title', 'problem_description', 'status', 'customer', 'customer_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'customer_name', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        user = obj.customer.user
        return f'{user.first_name} {user.last_name}'.strip() or user.username

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if 'status' in self.initial_data:
            raise serializers.ValidationError({'status': 'Use the ticket status endpoint to change status.'})
        if self.instance and self.instance.status in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
            raise serializers.ValidationError({'detail': 'Resolved or cancelled tickets cannot be modified.'})
        if user and user.is_authenticated and user.role == Authentication.ROLE_CHOICES.CUSTOMER:
            try:
                customer = Customers.objects.get(user=user)
            except Customers.DoesNotExist as exc:
                raise serializers.ValidationError({'customer': 'No customer profile is linked to this user.'}) from exc
            if self.instance is None:
                supplied = attrs.get('customer')
                if supplied and supplied.pk != customer.pk:
                    raise serializers.ValidationError({'customer': 'Customers can only create tickets for their own account.'})
                attrs['customer'] = customer
            elif self.instance.customer_id != customer.pk:
                raise serializers.ValidationError({'customer': 'Customers can only modify their own tickets.'})
        elif self.instance is None and 'customer' not in attrs:
            raise serializers.ValidationError({'customer': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        validated_data['status'] = Tickets.Status.OPEN
        return super().create(validated_data)


class TicketStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Tickets.Status.choices)
