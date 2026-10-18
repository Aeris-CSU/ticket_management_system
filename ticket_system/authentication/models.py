import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Authentication(AbstractUser):
    class ROLE_CHOICES(models.TextChoices):
        ADMIN = "ADMIN", 'admin'
        TECHNICIAN = "TECHNICIAN", 'technician'
        CUSTOMER = "CUSTOMER", 'customer'

    role = models.CharField(max_length=10, choices=ROLE_CHOICES.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OTPVerification(models.Model):
    MAX_ATTEMPTS = 3

    PURPOSE_CHOICES = (
        ('REGISTER', 'Registration'),
        ('RESET_PASSWORD', 'Reset Password'),
    )
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)  # <-- Tracks failed OTP verification attempts
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Expires in 10 minutes
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def has_exceeded_attempts(self):
        return self.attempts >= self.MAX_ATTEMPTS

    @staticmethod
    def generate_otp():
        return f"{random.randint(100000, 999999)}"


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        status_str = "SUCCESS" if self.successful else "FAILED"
        return f"{self.timestamp} - {self.username}: {status_str}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({'Read' if self.is_read else 'Unread'})"