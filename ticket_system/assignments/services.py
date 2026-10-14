from technicians.models import Technicians
from .models import Assignments


def release_technicians(technician_ids):
    """Called inside a transaction after deactivating assignments."""
    for technician in Technicians.objects.select_for_update().filter(pk__in=technician_ids).order_by('pk'):
        if not Assignments.objects.filter(technicians=technician, is_active=True).exists():
            technician.availability_status = Technicians.Availability.AVAILABLE
            technician.save(update_fields=['availability_status', 'updated_at'])
