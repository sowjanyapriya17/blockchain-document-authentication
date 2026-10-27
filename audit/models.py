from django.db import models


class AuditLog(models.Model):

    ACTION_CHOICES = [

        ('LOGIN', 'Login'),

        ('UPLOAD', 'Document Upload'),

        ('VERIFY', 'Document Verification'),

        ('UPDATE', 'Document Update'),

        ('REVOKE', 'Document Revoked'),

        ('BLOCKCHAIN', 'Blockchain Registration'),

        ('DOWNLOAD', 'Document Download'),

    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    description = models.TextField(
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.action