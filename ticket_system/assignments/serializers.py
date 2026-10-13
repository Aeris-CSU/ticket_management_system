from django.db import transaction
from rest_framework import serializers

from assignments.models import Assignments
from authentication.models import Authentication
from technicians.models import Technicians
from tickets.models import Tickets


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
            if technician.availability_status != Technicians.Availability.AVAILABLE:
                raise serializers.ValidationError({'technicians': 'The technician is not available.'})
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
        technician = Technicians.objects.get(pk=validated_data['technicians'].pk)
        if technician.availability_status != Technicians.Availability.AVAILABLE:
            raise serializers.ValidationError({'technicians': 'The technician is not available.'})
        if technician.user.role != Authentication.ROLE_CHOICES.TECHNICIAN:
            raise serializers.ValidationError({'technicians': 'The selected account is not a technician.'})
        if Assignments.objects.filter(tickets=ticket, is_active=True).exists():
            raise serializers.ValidationError({'tickets': 'This ticket already has an active assignment.'})
        validated_data['tickets'] = ticket
        validated_data['technicians'] = technician
        assignment = Assignments.objects.create(**validated_data)
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status', 'updated_at'])
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
        technician = Technicians.objects.get(pk=technician.pk)
        if technician.availability_status != Technicians.Availability.AVAILABLE:
            raise serializers.ValidationError({'technicians': 'The technician is not available.'})
        if technician.user.role != Authentication.ROLE_CHOICES.TECHNICIAN:
            raise serializers.ValidationError({'technicians': 'The selected account is not a technician.'})
        if Assignments.objects.filter(tickets=ticket, is_active=True).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError({'tickets': 'This ticket already has an active assignment.'})
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        replacement = Assignments.objects.create(tickets=ticket, technicians=technician)
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status', 'updated_at'])
        return replacement
