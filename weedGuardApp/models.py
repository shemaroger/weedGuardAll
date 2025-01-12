from datetime import timedelta
from django.conf import settings
from django.db import models,transaction
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
import logging
from django.contrib.postgres.fields import ArrayField

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
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.result} - {self.timestamp} - {self.site_name or 'Unknown Site'}"

    class Meta:
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"
