from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Technicians(AbstractUser):
    contact_number = models.CharField(max_length=11)
    specialization = models.CharField(max_length=100)
    availability_status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
