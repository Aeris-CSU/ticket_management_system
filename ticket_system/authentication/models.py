from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.
class Authentication(AbstractUser):
    class ROLE_CHOICES(models.TextChoices):
        ADMIN = "ADMIN", 'admin'
        TECHNICIAN = "TECHNICIAN", 'technician'
        CUSTOMER = "CUSTOMER", 'customer'
    role = models.CharField(max_length=10, choices=ROLE_CHOICES.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
