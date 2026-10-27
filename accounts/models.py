from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Admin'),
        ('ISSUER', 'Issuer'),
        ('VERIFIER', 'Verifier'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='VERIFIER'
    )

    is_approved = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"