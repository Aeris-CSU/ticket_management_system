from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class Technicians(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    availability_status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  # All fields
  # username=validated_data['username'],
  #           password=validated_data['password'],
  #           role = Authentication.ROLE_CHOICES.TECHNICIAN,
  #           first_name=validated_data.get('first_name', ''),
  #           last_name=validated_data.get('last_name', ''),
  #           email=validated_data.get('email', ''),