from django.db import models
from customers.models import Customers

# Create your models here.
class Tickets(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        ONGOING = 'ONGOING', 'Ongoing'
        RESOLVED = 'RESOLVED', 'Resolved'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.AutoField(primary_key=True)
    problem_title = models.CharField(max_length=200)
    problem_description = models.TextField()
    contact_number = models.CharField(max_length=30, blank=True, default='')
    address = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)

