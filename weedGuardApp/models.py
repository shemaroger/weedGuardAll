from datetime import timedelta
from django.conf import settings
from django.db import models,transaction
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
import logging
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
    )
    fullname = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Farmer')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']
    def __str__(self):
        return f"{self.fullname} ({self.role})"
    objects = CustomUserManager()
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Prediction(models.Model):
    image = models.ImageField(upload_to='predictions/')
    result = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)  # Use timezone.now for time zone-aware timestamps
    location = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.result} - {self.timestamp} - {self.site_name or 'Unknown Site'}"

    class Meta:
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Your Name")
    email = models.EmailField(verbose_name="Your Email")
    phone = models.CharField(
        max_length=15,
        verbose_name="Your Phone Number",
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    message = models.TextField(verbose_name="Your Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"