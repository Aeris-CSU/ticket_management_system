from django.utils import timezone
from authentication.notifications import notify_ticket
from django.db import transaction
from rest_framework import serializers

from assignments.models import Assignments
from authentication.models import Authentication
from technicians.models import Technicians
from tickets.models import Tickets
from .services import release_technicians


class AssignmentsSerializer(serializers.ModelSerializer):
    ticket_title = serializers.CharField(source='tickets.problem_title', read_only=True)
    technician_name = serializers.SerializerMethodField(read_only=True)
    technicians = serializers.PrimaryKeyRelatedField(queryset=Technicians.objects.select_related('user').all())

    class Meta:
        model = Assignments
        fields = ['id', 'tickets', 'ticket_title', 'technicians', 'technician_name', 'is_active', 'created_at', 'assigned_at']
        read_only_fields = ['id', 'ticket_title', 'technician_name', 'is_active', 'created_at', 'assigned_at']

    def get_technician_name(self, obj):
        user = obj.technicians.user
        return f'{user.first_name} {user.last_name}'.strip() or user.username

    def validate(self, attrs):
        ticket = attrs.get('tickets') or getattr(self.instance, 'tickets', None)
        technician = attrs.get('technicians') or getattr(self.instance, 'technicians', None)
        if self.instance and 'tickets' in attrs and attrs['tickets'].pk != self.instance.tickets_id:
            raise serializers.ValidationError({'tickets': 'An assignment record cannot be moved to another ticket.'})
        if self.instance and not self.instance.is_active:
            raise serializers.ValidationError({'detail': 'Inactive assignment history cannot be changed.'})
        if ticket and ticket.status in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
            raise serializers.ValidationError({'tickets': 'Resolved or cancelled tickets cannot be assigned.'})
        if ticket and technician:
            if technician.user.role != Authentication.ROLE_CHOICES.TECHNICIAN:
                raise serializers.ValidationError({'technicians': 'The selected account is not a technician.'})
            same_assignment = self.instance and technician.pk == self.instance.technicians_id
            if not same_assignment and technician.availability_status != Technicians.Availability.AVAILABLE:
                raise serializers.ValidationError({'technicians': 'The technician is not available.'})
            workload = Assignments.objects.filter(technicians=technician, is_active=True)
            if self.instance:
                workload = workload.exclude(pk=self.instance.pk)
            if workload.exists():
                raise serializers.ValidationError({'technicians': 'The technician already has an active ticket.'})
            duplicates = Assignments.objects.filter(tickets=ticket, is_active=True)
            if self.instance:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError({'tickets': 'This ticket already has an active assignment.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ticket = Tickets.objects.select_for_update().get(pk=validated_data['tickets'].pk)
        if ticket.status != Tickets.Status.OPEN:
            raise serializers.ValidationError({'tickets': 'Only open tickets can receive their first assignment.'})
        technician = Technicians.objects.select_for_update().get(pk=validated_data['technicians'].pk)
        if technician.availability_status != Technicians.Availability.AVAILABLE:
            raise serializers.ValidationError({'technicians': 'The technician is not available.'})
        if technician.user.role != Authentication.ROLE_CHOICES.TECHNICIAN:
            raise serializers.ValidationError({'technicians': 'The selected account is not a technician.'})
        if Assignments.objects.filter(tickets=ticket, is_active=True).exists():
            raise serializers.ValidationError({'tickets': 'This ticket already has an active assignment.'})
        if Assignments.objects.filter(technicians=technician, is_active=True).exists():
            raise serializers.ValidationError({'technicians': 'The technician already has an active ticket.'})
        validated_data['tickets'] = ticket
        validated_data['technicians'] = technician
        assignment = Assignments.objects.create(**validated_data)
        technician.availability_status = Technicians.Availability.UNAVAILABLE
        technician.save(update_fields=['availability_status', 'updated_at'])
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status', 'updated_at'])
        notify_ticket(ticket, 'ASSIGNED', technician=technician)
        return assignment

    @transaction.atomic
    def update(self, instance, validated_data):
        ticket = Tickets.objects.select_for_update().get(pk=instance.tickets_id)
        instance = Assignments.objects.select_for_update().get(pk=instance.pk)
        technician = validated_data.get('technicians', instance.technicians)
        if technician.pk == instance.technicians_id:
            return instance
        if ticket.status not in (Tickets.Status.ASSIGNED, Tickets.Status.ONGOING):
            raise serializers.ValidationError({'tickets': 'Only assigned or ongoing tickets can be reassigned.'})
        locked = {person.pk: person for person in Technicians.objects.select_for_update().filter(pk__in=[instance.technicians_id, technician.pk]).order_by('pk')}
        technician = locked[technician.pk]
        if technician.availability_status != Technicians.Availability.AVAILABLE:
            raise serializers.ValidationError({'technicians': 'The technician is not available.'})
        if technician.user.role != Authentication.ROLE_CHOICES.TECHNICIAN:
            raise serializers.ValidationError({'technicians': 'The selected account is not a technician.'})
        if Assignments.objects.filter(tickets=ticket, is_active=True).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError({'tickets': 'This ticket already has an active assignment.'})
        if Assignments.objects.filter(technicians=technician, is_active=True).exists():
            raise serializers.ValidationError({'technicians': 'The technician already has an active ticket.'})
        instance.is_active = False
        instance.ended_at = timezone.now()
        instance.end_reason = 'REASSIGNED'
        instance.save(update_fields=['is_active', 'ended_at', 'end_reason'])
        replacement = Assignments.objects.create(tickets=ticket, technicians=technician)
        technician.availability_status = Technicians.Availability.UNAVAILABLE
        technician.save(update_fields=['availability_status', 'updated_at'])
        release_technicians([instance.technicians_id])
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status', 'updated_at'])
        notify_ticket(ticket, 'ASSIGNED', technician=technician, previous=instance.technicians)
        return replacement


class AssignmentHistorySerializer(serializers.ModelSerializer):
    ticket_id = serializers.IntegerField(source='tickets_id', read_only=True)
    ticket_number = serializers.CharField(source='tickets.ticket_number', read_only=True)
    problem_title = serializers.CharField(source='tickets.problem_title', read_only=True)
    problem_description = serializers.CharField(source='tickets.problem_description', read_only=True)
    current_status = serializers.CharField(source='tickets.status', read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignments
        fields = ['id', 'ticket_id', 'ticket_number', 'problem_title', 'problem_description', 'current_status', 'customer_name', 'created_at', 'ended_at', 'end_reason']
        read_only_fields = fields

    def get_customer_name(self, obj):
        user = obj.tickets.customer.user
        return f'{user.first_name} {user.last_name}'.strip() or user.username
