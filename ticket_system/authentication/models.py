from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.
class Authentication(AbstractUser):
    class ROLE_CHOICES(models.TextChoices):
        ADMIN = "ADMIN", 'admin'
        TECHNICIAN = "TECHNICIAN", 'technician'
        CUSTOMER = "CUSTOMER", 'customer'
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    recipient = models.ForeignKey(Authentication, on_delete=models.CASCADE, related_name='notifications')
    ticket = models.ForeignKey('tickets.Tickets', null=True, on_delete=models.SET_NULL)
    event = models.CharField(max_length=30)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['recipient', 'is_read', '-created_at'])]
