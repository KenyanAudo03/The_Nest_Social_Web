from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta
from django.utils.timezone import now
import datetime

User = get_user_model()


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.created_at + timedelta(hours=1)  

    def __str__(self):
        return f"Verification token for {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """Token expires after 15 minutes"""
        return now() < self.created_at + timedelta(minutes=15)
