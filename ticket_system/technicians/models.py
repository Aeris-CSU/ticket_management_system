from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Technicians(AbstractUser):
    contact_number = models.CharField(max_length=11)
    is_admin = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    specialization = models.CharField(max_length=100)
    availability_status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
