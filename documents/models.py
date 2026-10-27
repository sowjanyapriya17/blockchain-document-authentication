from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
        ('ARCHIVED', 'Archived'),
    ]

    DOCUMENT_TYPES = [
        ('CERTIFICATE', 'Certificate'),
        ('MARKSHEET', 'Mark Sheet'),
        ('DIPLOMA', 'Diploma'),
        ('DEGREE', 'Degree'),
        ('INTERNSHIP', 'Internship Certificate'),
        ('TRAINING', 'Training Certificate'),
        ('LICENSE', 'License'),
        ('AGREEMENT', 'Agreement'),
        ('REPORT', 'Report'),
        ('OTHER', 'Other'),
    ]

    document_id = models.CharField(
        max_length=50,
        unique=True
    )

    title = models.CharField(
        max_length=200
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES
    )

    description = models.TextField(
        blank=True
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to='documents/'
    )

    document_hash = models.CharField(
        max_length=64,
        blank=True
    )

    issue_date = models.DateField()

    expiry_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.document_id


class DocumentVersion(models.Model):

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    version_number = models.PositiveIntegerField()

    file = models.FileField(
        upload_to='document_versions/'
    )

    document_hash = models.CharField(
        max_length=64
    )

    digital_signature = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_current = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.document.document_id} - Version {self.version_number}"