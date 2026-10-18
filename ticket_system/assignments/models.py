from django.db import models
from tickets.models import Tickets
from technicians.models import Technicians

# Create your models here.
class Assignments(models.Model):
    id = models.AutoField(primary_key=True)
    tickets = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    technicians = models.ForeignKey(Technicians, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(auto_now=True)
