from rest_framework import serializers
from assignments.models import Assignments

class AssignmentsSerializer(serializers.ModelSerializer):
    ticket_title = serializers.CharField(source='tickets.problem_title', read_only=True)
    technician_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Assignments
        fields = [
            'id',
            'tickets',
            'ticket_title',
            'technicians',
            'technician_name',
            'created_at',
            'assigned_at',
        ]
        read_only_fields = ['id', 'ticket_title', 'technician_name', 'created_at', 'assigned_at']

    def get_technician_name(self, obj):
        user = obj.technicians.user
        return f'{user.first_name} {user.last_name}'.strip() or user.username

    def validate_tickets(self, value):
        if value.status in ['RESOLVED', 'CLOSED']:
            raise serializers.ValidationError('Resolved or closed tickets cannot be assigned.')
        return value

    def validate(self, attrs):
        tickets = attrs.get('tickets') or getattr(self.instance, 'tickets', None)
        technicians = attrs.get('technicians') or getattr(self.instance, 'technicians', None)

        if tickets and technicians:
            duplicate = Assignments.objects.filter(tickets=tickets, technicians=technicians)
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError('This ticket is already assigned to that technician.')
        return attrs

    def create(self, validated_data):
        assignment = super().create(validated_data)
        ticket = assignment.tickets
        if ticket.status == 'OPEN':
            ticket.status = 'ASSIGNED'
            ticket.save(update_fields=['status', 'updated_at'])
        return assignment

    def update(self, instance, validated_data):
        assignment = super().update(instance, validated_data)
        ticket = assignment.tickets
        if ticket.status == 'OPEN':
            ticket.status = 'ASSIGNED'
            ticket.save(update_fields=['status', 'updated_at'])
        return assignment

