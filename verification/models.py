from django.db import models


class Verification(models.Model):

    METHOD_CHOICES = [
        ('DOCUMENT_ID', 'Document ID'),
        ('DOCUMENT_UPLOAD', 'Document Upload'),
        ('QR_CODE', 'QR Code'),
    ]

    RESULT_CHOICES = [
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
        ('NOT_FOUND', 'Not Found'),
    ]

    verification_id = models.CharField(
        max_length=100,
        unique=True
    )

    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    method = models.CharField(
        max_length=30,
        choices=METHOD_CHOICES
    )

    generated_hash = models.CharField(
        max_length=64,
        blank=True
    )

    blockchain_hash = models.CharField(
        max_length=64,
        blank=True
    )

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES
    )

    verified_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.verification_id