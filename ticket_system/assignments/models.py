from django.db import models
from tickets.models import Tickets
from technicians.models import Technicians

# Create your models here.
class Assignments(models.Model):
    id = models.AutoField(primary_key=True)
    tickets = models.ForeignKey(Tickets, on_delete=models.PROTECT)
    technicians = models.ForeignKey(Technicians, blank=True, on_delete=models.PROTECT)
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=20, blank=True, default='', choices=[('RESOLVED', 'Resolved'), ('CANCELLED', 'Cancelled'), ('REASSIGNED', 'Reassigned away'), ('UNASSIGNED', 'Unassigned')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['technicians'], condition=models.Q(is_active=True),
                name='one_active_assignment_per_technician',
            ),
            models.UniqueConstraint(
                fields=['tickets'],
                condition=models.Q(is_active=True),
                name='one_active_assignment_per_ticket',
            ),
        ]
