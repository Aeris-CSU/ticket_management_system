from django.db import transaction
from customers.phone import validate_mobile_number
from rest_framework import serializers

from authentication.models import Authentication
from customers.models import Customers
from .models import Tickets


class TicketsSerializer(serializers.ModelSerializer):
    def validate_contact_number(self, value):
        return validate_mobile_number(value)

    customer_name = serializers.SerializerMethodField(read_only=True)
    customer_address = serializers.CharField(source='address', read_only=True)
    address = serializers.CharField(max_length=100, required=False)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customers.objects.select_related('user').all(), required=False)

    class Meta:
        model = Tickets
        fields = ['id', 'ticket_number', 'problem_title', 'problem_description', 'contact_number', 'address', 'status', 'cancellation_reason', 'customer', 'customer_name', 'customer_address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'ticket_number', 'ticket_number', 'status', 'cancellation_reason', 'customer_name', 'created_at', 'updated_at']

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
            if self.instance:
                if self.instance.status != Tickets.Status.OPEN:
                    raise serializers.ValidationError({'detail': 'Customers can only edit open tickets before assignment.'})
                if 'customer' in attrs and attrs['customer'].pk != customer.pk:
                    raise serializers.ValidationError({'customer': 'You cannot change the ticket owner.'})
        elif self.instance is None and 'customer' not in attrs:
            raise serializers.ValidationError({'customer': 'This field is required.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        customer = validated_data['customer']
        validated_data.setdefault('address', customer.address)
        validated_data.setdefault('contact_number', customer.contact_number)
        validated_data['status'] = Tickets.Status.OPEN
        ticket = super().create(validated_data)
        from authentication.notifications import notify_ticket
        notify_ticket(ticket, 'SUBMITTED')
        return ticket


class TicketStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Tickets.Status.choices)
    cancellation_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)
